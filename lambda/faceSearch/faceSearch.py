import boto3
import base64
from cutImage import image_splite

class FaceSearch:
    def __init__(self, dataModel, aws_access_key_id, aws_secret_access_key, region_name, collection_id):
        self.__dataModel = dataModel
        self.__aws_access_key_id = aws_access_key_id
        self.__aws_secret_access_key = aws_secret_access_key
        self.__region_name = region_name
        self.__collection_id = collection_id
        self.__faceValidationModel = {
            "state":"faceValidation",
            "validationResult" : {}
        }
    def faceSearch(self, memberUrlList, memberIdList):
        client = boto3.client('rekognition',aws_access_key_id =  self.__aws_access_key_id,aws_secret_access_key = self.__aws_secret_access_key, region_name = self.__region_name)
        threshold = self.__dataModel["config"]["faceValidationThreshold"]
        image_binary = base64.b64decode(self.__dataModel["frame"]["OpenCV"]["imageBase64"])
        matchingFaceList = []
        
        if self.__dataModel["faceDetection"]["detectionResult"]["faceCount"] == 1:
            
            self.__response=client.search_faces_by_image(CollectionId=self.__collection_id,
                                    Image={'Bytes':image_binary},
                                    FaceMatchThreshold=threshold,
                                    MaxFaces=10)
            matchingCount = len(self.__response["FaceMatches"])
            if matchingCount !=0:
                
                matchingFaceList.append({
                    "faceId": self.__response["FaceMatches"][0]["Face"]["FaceId"],
                    "similarity":self.__response["FaceMatches"][0]["Similarity"],
                    "targetImageUrl": memberUrlList[self.__response["FaceMatches"][0]["Face"]["FaceId"]],
                    "targetBoundingBox": self.__response["FaceMatches"][0]["Face"]["BoundingBox"],
                    "sourceBoundingBox": self.__response["SearchedFaceBoundingBox"],
                    "targetId":memberIdList[self.__response["FaceMatches"][0]["Face"]["FaceId"]]
                })
            # else:
            #         matchingFaceList.append({
            #             "faceId": "",
            #             "similarity":0,
            #             "targetImageUrl": "",
            #             "targetId":"",
            #             "targetBoundingBox": {},
            #             "sourceBoundingBox": self.__dataModel["faceDetection"]["detectionResult"]["faceList"][0]["boundingBox"]
            #         })
            
        else:
            faceBoundingBox = []
            for face in self.__dataModel["faceDetection"]["detectionResult"]["faceList"]:
                faceBoundingBox.append(face["boundingBox"])
            faceImageList = image_splite(image_binary,faceBoundingBox)
            faceBoundingBoxIndex = 0
            for faceImage in faceImageList:
                
                response=client.search_faces_by_image(CollectionId=self.__collection_id,
                                    Image={'Bytes':faceImage},
                                    FaceMatchThreshold=threshold,
                                    MaxFaces=10)
                
                if len(response["FaceMatches"]) !=0:
                    # print("YAAA: ", response["FaceMatches"][0]["Face"]["FaceId"])
                    matchingFaceList.append({
                        "faceId": response["FaceMatches"][0]["Face"]["FaceId"],
                        "similarity":response["FaceMatches"][0]["Similarity"],
                        "targetImageUrl": memberUrlList[response["FaceMatches"][0]["Face"]["FaceId"]],
                        "targetId":memberIdList[response["FaceMatches"][0]["Face"]["FaceId"]],
                        "targetBoundingBox": response["FaceMatches"][0]["Face"]["BoundingBox"],
                        "sourceBoundingBox": faceBoundingBox[faceBoundingBoxIndex]
                    })
                # else:
                #     matchingFaceList.append({
                #         "faceId": "",
                #         "similarity":0,
                #         "targetImageUrl": "",
                #         "targetId":"",
                #         "targetBoundingBox": {},
                #         "sourceBoundingBox": faceBoundingBox[faceBoundingBoxIndex]
                #     })
                faceBoundingBoxIndex = faceBoundingBoxIndex + 1
                
        validationResult = {
            "matchedFaceList": matchingFaceList,
        }
        
        self.__faceValidationModel["validationResult"] = validationResult

            
    def getModel(self):
        return self.__faceValidationModel