import cv2
import requests
import json
import uvicorn
import traceback
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from fastapi.responses import JSONResponse
from requests_toolbelt.multipart.encoder import MultipartEncoder
import os
from cam_handler import Camera_handler, global_data

cam = Camera_handler()

TOKEN_URL = 'https://rs.vastcommerce.in/rscane/control/generateAuthToken'
SEND_IMAGES_URL = 'https://rs.vastcommerce.in/api/rest/rs/v1/create-vehicleImageDetails'
DEFAULT_HEADER = {
    'Content-Type': 'application/json',
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.5 (KHTML, like Gecko) Chrome/19.0.1084.52 Safari/536.5'
}
CAMERA_PARAMETER_NAME=["frontView_img","backView_img","sideView_img","topView_img"]

app = FastAPI(redoc_url=None, docs_url='/documentation')

origins = [
   "http://localhost.tiangolo.com",
   "https://localhost.tiangolo.com",
   "http://localhost",
   "http://localhost:3000",
   "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ItemResult:
    def __init__(self, width, height, xmin, ymin, xmax, ymax, confidence, imagePath):
        self.width = width
        self.height = height
        self.xmin = xmin
        self.ymin = ymin
        self.xmax = xmax
        self.ymax = ymax
        self.confidence = confidence
        self.imagePath = imagePath

@app.get('/detect')
async def cvDetection(rfidStr: str, location: str):
    print(rfidStr)
    print('API - Enter into detection')
    try:
        startTime = datetime.now()
        requestId = str(int(startTime.timestamp()))
        imagePath = "images/" +  requestId
        os.mkdir(imagePath)
        cvImageList = []

        imagesList= {
            "rfid" : rfidStr,
            "location" : location
        }

        for index, cameraurl in enumerate(global_data.get('cam_url'), start=1) : 
            ret, frame, _ = cam.read_frame(cameraurl)
            print(index)
            if ret:
                cvImageList.append(frame)
                path = imagePath + "/" + str(index) + ".png"
                cv2.imwrite(path, frame)
                imagesList[CAMERA_PARAMETER_NAME[index-1]] = (f'{index}.png', open(f'{path}', 'rb'), 'image/png')

        response = {}

        #Gathering Token
        tokenHeaders = DEFAULT_HEADER
        tokenHeaders["clientId"] = "MupbFnwbPcic1I2h92NQshqCe7tv3MH2"
        tokenHeaders["secretKey"] = "tAiSNcMyjtPTtfMFMu0t6zvjj0SL+ynwneXO/SIU17g="
        tokenResp = requestGetMethod(tokenHeaders, TOKEN_URL)
        tokenData = tokenResp.json()
        print(tokenData)
        if tokenData and tokenData['userLoginMap'] and tokenData['userLoginMap']['authToken']: 
            imagesHeaders = DEFAULT_HEADER
            imagesHeaders["Authorization"] = "Bearer "+ tokenData['userLoginMap']['authToken']
            imagesHeaders["Content-Type"] = "multipart/form-data"
            multipart_data = MultipartEncoder(
                fields = imagesList
            )
            imagesHeaders["Content-Type"] = multipart_data.content_type
            print(imagesList)
            session = requests.Session()
            imageProcessingResponse = session.post(SEND_IMAGES_URL, data=multipart_data, headers=imagesHeaders)
            imageProcessingData = imageProcessingResponse.json()
            response = imageProcessingResponse
            print(imageProcessingData)
        endTime = datetime.now()
        print('API - Process completed - ', endTime - startTime)
        return JSONResponse(content=response.json())
    except:
        print(traceback.format_exc())
    return {}

def requestPostMethod(headers, payload, URL) : 
    return requests.post(URL, data=json.dumps(payload), headers=headers)

def requestGetMethod(headers, URL) : 
    return requests.get(URL, headers=headers)

def main():
   uvicorn.run(app, host ='0.0.0.0', port=8084)

if __name__ == '__main__':
   uvicorn.run(app, host ='0.0.0.0', port=8084)  
