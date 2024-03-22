import cv2
import base64
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
from ultralytics import YOLO
from cam_handler import Camera_handler, global_data
#imports_gaurav
from config import get_db
import models
from crud import insert_rfid,search_rfid,insert_audit
from config import engine
models.Base.metadata.create_all(bind=engine)
db=get_db()
cam = Camera_handler()

OCR_URL = 'http://localhost:9002/getOcr'
TOKEN_URL = 'https://rs.vastcommerce.in/rscane/control/generateAuthToken'
SEND_IMAGES_URL = 'https://rs.vastcommerce.in/api/rest/rs/v1/create-gateEntry-details'
DEFAULT_HEADER = {
    'Content-Type': 'application/json',
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.5 (KHTML, like Gecko) Chrome/19.0.1084.52 Safari/536.5'
}
IS_YOLO_DETECTION = True

if IS_YOLO_DETECTION : 
    yoloV8model = YOLO('best.pt')

#app = FastAPI(redoc_url=None, docs_url='/documentation')
app=FastAPI()
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

@app.post('/insert_rfid')
async def rfid(rfid:str):
    try:
        insert_crud=insert_rfid(db,rfid=rfid)
        return "record inserted successfully" 
    except:
        return "not able to insert the record" 



@app.post('/detect')
async def cvDetection(rfidStr:str,location:str,ip:str):
    rfid=search_rfid(db,rfid=rfidStr)
    if rfid:   
        print(rfidStr)
        print('API - Enter into detection')
        try:
            startTime = datetime.now()
            requestId = str(int(startTime.timestamp()))
            imagePath = "images/" +  requestId
            os.mkdir(imagePath)
            cvImageList = []

            imagesList= {
                "rfid" : rfidStr
            }

            for index, cameraurl in enumerate(global_data.get('cam_url'), start=1) : 
                ret, frame, _ = cam.read_frame(cameraurl)
                if ret:
                    # image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    cvImageList.append(frame)
                    path = imagePath + "/" + str(index) + ".png"
                    cv2.imwrite(path, frame)
                    imagesList[f'uploadedFile_{index}'] = (f'{index}.png', open(f'{path}', 'rb'), 'image/png')

            response = {}
            if IS_YOLO_DETECTION : 
                # filePath = "test-images/15.jpeg"
                saveDetectionPath = imagePath + "/prediction"
                os.mkdir(saveDetectionPath)

                detectionResult = yoloV8model.predict(cvImageList, save=True, project=saveDetectionPath)

                result=[]
            
                for detection in detectionResult :
                    result =  [ItemResult(r[2], r[3], r1[0], r1[1], r1[2], r1[3], conf ,path)for r, r1, conf, path in zip(detection.boxes.xywh.cpu().numpy(), detection.boxes.xyxy.cpu().numpy(), detection.boxes.conf.cpu().numpy(), detection.path)]

                print("Number of Detection License Plate", len(result))
                highConfidence = 0
                highConfidenceIndex = None
                if len(result) > 0 :
                    for index, detection in enumerate(result, start=0) :
                        if detection.confidence > highConfidence :
                            highConfidence = detection.confidence
                            highConfidenceIndex = index
                    predictedResult = result[highConfidenceIndex]
                    image = cv2.imread(saveDetectionPath+"/predict"+predictedResult.imagePath)
                    image = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                    xmin = int(predictedResult.xmin)
                    ymin = int(predictedResult.ymin)
                    xmax = int(predictedResult.xmax)
                    ymax = int(predictedResult.ymax)

                    print("x------>" , xmin, xmax, ymin, ymax)
                
                    segment_frame = image[ymin:ymax, xmin:xmax]

                    ret, buffer = cv2.imencode('.jpg', segment_frame)
                    base64Str = str(base64.b64encode(buffer), 'UTF-8')

                    cv2.imwrite("cropped.png", segment_frame)

                    # OCR Processing
                    ocrPayload = {
                        "imageUrl": base64Str
                    }
                    ocrResp = requestPostMethod(DEFAULT_HEADER, ocrPayload, OCR_URL)
                    ocrData = ocrResp.json()
                    if ocrData and ocrData['pages'] : 
                        response['vehicleNumber'] = ocrData['pages']
                        print(ocrData['pages']) 

                
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
                rfid_unique_id="w21212"
                details={"k1":123}
                audit=insert_audit(db,fid=rfid.id,
                                    rfid_unique_id=rfid_unique_id,
                                    rfid_ipadress=ip,
                                    location=str(location),
                                    details=str(details),
                                    external_api_url=str(SEND_IMAGES_URL),
                                    )
                print(imageProcessingData)
            endTime = datetime.now()
            print('API - Process completed - ', endTime - startTime)
            return JSONResponse(content=response.json())
        except:
            print(traceback.format_exc())
        return {}
    else:
        return "rfid not found"    

def requestPostMethod(headers, payload, URL) : 
    return requests.post(URL, data=json.dumps(payload), headers=headers)

def requestGetMethod(headers, URL) : 
    return requests.get(URL, headers=headers)

# def main():
#    uvicorn.run(app, host ='0.0.0.0', port=8084)

# if __name__ == '__main__':
#    uvicorn.run(app, host ='0.0.0.0', port=8084)  
