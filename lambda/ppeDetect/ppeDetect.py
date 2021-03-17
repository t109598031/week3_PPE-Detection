import boto3
import base64
# from cutImage import image_splite
import copy

class PpeDetection:
    def __init__(self, dataModel, aws_access_key_id, aws_secret_access_key, region_name):
        self.__dataModel = dataModel
        self.__aws_access_key_id = aws_access_key_id
        self.__aws_secret_access_key = aws_secret_access_key
        self.__region_name = region_name
        self.__ppeDetectionModel = {
            "state":"ppeDetection",
            "ppeDetectionResult":{}
        }
        
    def ppeDetect(self):
        client = boto3.client('rekognition',aws_access_key_id =  self.__aws_access_key_id,aws_secret_access_key = self.__aws_secret_access_key, region_name = self.__region_name)
        self.__response = client.detect_protective_equipment(Image={'S3Object':{'Bucket':self.__dataModel["faceDetection"]["s3"]["s3BucketName"],'Name':self.__dataModel["frame"]["captureResult"]["id"]}},
                                                            SummarizationAttributes={'MinConfidence':self.__dataModel["config"]["ppeDetectionThreshold"], 'RequiredEquipmentTypes':['FACE_COVER', 'HAND_COVER', 'HEAD_COVER']}
        )
        personList = []
        emptyDict = {}
        violationCount = 0
        for person in self.__response["Persons"]:
            personModel = copy.deepcopy(emptyDict)
            personModel["boundingBox"] = person["BoundingBox"]
            personModel["face_cover"] = False
            personModel["face_cover_confidence"] = 0
            personModel["head_cover"] = False
            personModel["head_cover_confidence"] = 0
            personModel["left_hand_cover"] = False
            personModel["left_hand_cover_confidence"] = 0
            personModel["right_hand_cover"] = False
            personModel["right_hand_cover_confidence"] = 0
            for bodyPart in person["BodyParts"]:
                if bodyPart["Name"] == "FACE" and len(bodyPart["EquipmentDetections"])!=0:
                    personModel["face_cover"] = True
                    personModel["face_cover_confidence"] = bodyPart["EquipmentDetections"][0]["Confidence"]
                    
                if bodyPart["Name"] == "HEAD" and len(bodyPart["EquipmentDetections"])!=0:
                    personModel["head_cover"] = True
                    personModel["head_cover_confidence"] = bodyPart["EquipmentDetections"][0]["Confidence"]
                    
                if bodyPart["Name"] == "LEFT_HAND" and len(bodyPart["EquipmentDetections"])!=0:
                    personModel["left_hand_cover"] = True
                    personModel["left_hand_cover_confidence"] = bodyPart["EquipmentDetections"][0]["Confidence"]
                    
                if bodyPart["Name"] == "RIGHT_HAND" and len(bodyPart["EquipmentDetections"])!=0:
                    personModel["right_hand_cover"] = True
                    personModel["right_hand_cover_confidence"] = bodyPart["EquipmentDetections"][0]["Confidence"]
                    
            personList.append(personModel)
            
            
        self.__ppeDetectionModel["ppeDetectionResult"]["personList"] = personList
        
    def getModel(self):
        return self.__ppeDetectionModel