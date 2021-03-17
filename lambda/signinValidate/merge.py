import copy
import psycopg2
from datetime import datetime
import json
import copy
import config

class MergeResult:
    def __init__(self, dataModel):
        self.__result = dataModel
        self.__result["faceValidateAndPpeDetect"] = {}
        
    def merge_ppe_faceValidation(self):
        for resultModel in self.__result["ParallelResultPath"]:
            if resultModel["state"] == "faceValidation":
                faceValidationModel = resultModel["validationResult"]
            elif resultModel["state"] == "ppeDetection":
                ppeDetectionModel = resultModel["ppeDetectionResult"]
        
        capture = {
            "frameId": self.__result["frame"]["captureResult"]["id"],
            "timestamp": self.__result["frame"]["captureResult"]["timestamp"],
            "sourceImageUrl": self.__result["faceDetection"]["s3"]["sourceImageUrl"]
            # "s3BucketName": self.__result["faceDetection"]["s3"]["s3BucketName"]
        }
        emptyDict = {}
        # signinValidateModel = copy.deepcopy(emptyDict)
        signinValidateModel = {
            "faceCount": self.__result["faceDetection"]["detectionResult"]["faceCount"], # 來源人數
            "memberCount": len(faceValidationModel["matchedFaceList"]), # 成員人數
            "notMemberCount":0, # 非成員人數
            "validPpeCount":0, # 合格人數
            "validSigninCount":0, # 成功簽到人數
            "ppeResult":"皆依規定配戴" # 皆依規定配戴、未依規定配戴
        }
        sourceImageMemberList = []
        sourceImagePersonList = []
        
        
        for person in ppeDetectionModel["personList"]:
            personModel = copy.deepcopy(emptyDict)
            personModel["ppeDetection"] = {}
            personModel["ppeDetection"]["face"] = {
                "face_cover":person["face_cover"],
                "face_cover_confidence":person["face_cover_confidence"]
            }
            personModel["ppeDetection"]["head"] = {
                "head_cover":person["head_cover"],
                "head_cover_confidence":person["head_cover_confidence"]
            }
            personModel["ppeDetection"]["left_hand"] = {
                "left_hand_cover":person["left_hand_cover"],
                "left_hand_cover_confidence":person["left_hand_cover_confidence"]
            }
            personModel["ppeDetection"]["right_hand"] = {
                "right_hand_cover":person["right_hand_cover"],
                "right_hand_cover_confidence":person["right_hand_cover_confidence"]
            }
            
            personModel["isMember"] = False
            personModel["faceId"] = ""
            personModel["targetImageUrl"] = ""
            personModel["targetId"] = ""
            personModel["similarity"] = 0

            for matchedFace in faceValidationModel["matchedFaceList"]:
                if (person["boundingBox"]["Left"] <= matchedFace["sourceBoundingBox"]["Left"] 
                and person["boundingBox"]["Top"] <= matchedFace["sourceBoundingBox"]["Top"]
                and person["boundingBox"]["Left"] + person["boundingBox"]["Width"] >= matchedFace["sourceBoundingBox"]["Left"] + matchedFace["sourceBoundingBox"]["Width"]
                and person["boundingBox"]["Top"] + person["boundingBox"]["Height"] >= matchedFace["sourceBoundingBox"]["Top"] + matchedFace["sourceBoundingBox"]["Height"]
                ):
                    personModel["isMember"] = True
                    personModel["faceId"] = matchedFace["faceId"]
                    personModel["targetImageUrl"] = matchedFace["targetImageUrl"]
                    personModel["targetId"] = matchedFace["targetId"]
                    personModel["similarity"] = matchedFace["similarity"]            
                    
            if ((personModel["ppeDetection"]["face"]["face_cover"] == False and self.__result["config"]["maskDetection"] == True)
            or (personModel["ppeDetection"]["head"]["head_cover"] == False and self.__result["config"]["helmetDetection"] == True)
            or (personModel["ppeDetection"]["left_hand"]["left_hand_cover"] == False and self.__result["config"]["glovesDetection"] == True)
            or (personModel["ppeDetection"]["right_hand"]["right_hand_cover"] == False and self.__result["config"]["glovesDetection"] == True)):
                personModel["violation"] = True
                signinValidateModel["ppeResult"] = "未依規定配戴"
            else:
                personModel["violation"] = False
                signinValidateModel["validPpeCount"] = signinValidateModel["validPpeCount"] + 1
            
            personModel["validSignin"] = False
            if personModel["isMember"] == True:
                if personModel["violation"] == False:
                    personModel["validSignin"] = True
                    signinValidateModel["validSigninCount"] = signinValidateModel["validSigninCount"] + 1
                    personModel["signinResult"] = "成員依規定配戴"
                elif personModel["violation"] == True:
                    personModel["signinResult"] = "成員未依規定配戴"
            elif personModel["isMember"] == False:
                signinValidateModel["notMemberCount"] = signinValidateModel["notMemberCount"] + 1
                if personModel["violation"] == False:
                    personModel["signinResult"] = "非成員擅入警示"
                elif personModel["violation"] == True:
                    personModel["signinResult"] = "非成員危險警示"
                    
            personModel["faceConfidence"] = 30.0995
            personModel["faceCoordinate"] = {
                "X":0.91,
                "Y":0.01
            }
            # personModel["faceCoordinate"] = {}
            
            
            for detectedFace in self.__result["faceDetection"]["detectionResult"]["faceList"]:
                if (person["boundingBox"]["Left"] <= detectedFace["boundingBox"]["Left"] 
                and person["boundingBox"]["Top"] <= detectedFace["boundingBox"]["Top"]
                and person["boundingBox"]["Left"] + person["boundingBox"]["Width"] >= detectedFace["boundingBox"]["Left"] + detectedFace["boundingBox"]["Width"]
                and person["boundingBox"]["Top"] + person["boundingBox"]["Height"] >= detectedFace["boundingBox"]["Top"] + detectedFace["boundingBox"]["Height"]
                ):
                    personModel["faceConfidence"] = detectedFace["confidence"]
                    personModel["faceCoordinate"]["X"] = detectedFace["boundingBox"]["Left"] + 0.5*detectedFace["boundingBox"]["Width"]
                    personModel["faceCoordinate"]["Y"] = detectedFace["boundingBox"]["Top"] + 0.5*detectedFace["boundingBox"]["Height"]
            sourceImagePersonList.append(personModel)            
        for matchedFace in faceValidationModel["matchedFaceList"]:
            sourceImageMemberList.append({
                "targetImageUrl": matchedFace["targetImageUrl"],
                "similarity": matchedFace["similarity"]
            })
                    
        self.__outputResult = {
            "capture":capture,
            "signinValidate": signinValidateModel,
            "sourceImagePersonList": sourceImagePersonList,
            "sourceImageMemberList": sourceImageMemberList
        }        
        # sourceImagePersonList = []
        # personModel = {}
        # for person in ppeDetectionModel["personList"]:
        #     personModel = copy.deepcopy(personModel)
        #     personModel["sourcePersonBoundingBox"] = person["boundingBox"]
        #     personModel["ppeResult"] = {}
        #     personModel["ppeResult"]["face"] = {
        #         "face_cover":person["face_cover"],
        #         "face_cover_confidence":person["face_cover_confidence"]
        #     }
        #     personModel["ppeResult"]["head"] = {
        #         "head_cover":person["head_cover"],
        #         "head_cover_confidence":person["head_cover_confidence"]
        #     }
        #     personModel["ppeResult"]["left_hand"] = {
        #         "left_hand_cover":person["left_hand_cover"],
        #         "left_hand_cover_confidence":person["left_hand_cover_confidence"]
        #     }
        #     personModel["ppeResult"]["right_hand"] = {
        #         "right_hand_cover":person["right_hand_cover"],
        #         "right_hand_cover_confidence":person["right_hand_cover_confidence"]
        #     }
            
        #     personModel["faceId"] = ""
        #     personModel["targetImageUrl"] = ""
        #     personModel["targetId"] = ""
        #     personModel["similarity"] = 0
        #     personModel["targetFaceBoundingBox"] = {}
        #     personModel["sourceFaceBoundingBox"] = {}
            
        #     for matchedFace in faceValidationModel["matchedFaceList"]:
        #         if (person["boundingBox"]["Left"] <= matchedFace["sourceBoundingBox"]["Left"] 
        #         and person["boundingBox"]["Top"] <= matchedFace["sourceBoundingBox"]["Top"]
        #         and person["boundingBox"]["Left"] + person["boundingBox"]["Width"] >= matchedFace["sourceBoundingBox"]["Left"] + matchedFace["sourceBoundingBox"]["Width"]
        #         and person["boundingBox"]["Top"] + person["boundingBox"]["Height"] >= matchedFace["sourceBoundingBox"]["Top"] + matchedFace["sourceBoundingBox"]["Height"]
        #         ):
        #             personModel["faceId"] = matchedFace["faceId"]
        #             personModel["targetImageUrl"] = matchedFace["targetImageUrl"]
        #             personModel["targetId"] = matchedFace["targetId"]
        #             personModel["similarity"] = matchedFace["similarity"]
        #             personModel["targetFaceBoundingBox"] = matchedFace["targetBoundingBox"]
        #             personModel["sourceFaceBoundingBox"] = matchedFace["sourceBoundingBox"]
        #             break
        #     sourceImagePersonList.append(personModel)
        #     self.__result["faceValidateAndPpeDetect"]["sourceImagePersonList"] = sourceImagePersonList
            
        #     self.__result["frame"]["OpenCV"]["imageBase64"] = ""
        #     self.__result["ParallelResultPath"] = ""
    def redshiftInject(self):
        model = copy.deepcopy(self.__outputResult)
        conn = psycopg2.connect(dbname=config.dbname, host=config.host, port=config.port, user=config.user, password=config.password)
        cur = conn.cursor();    
        
        for i in range(model['signinValidate']['faceCount']):

            cur.execute("insert into ppe_analytics ("+
            "frameid,"+
            "frametimestamp,"+
            "facecount,"+
            "sourceimageurl,"+
            "targetimageurl,"+
            
            "membercount,"+
            "faceid,"+
            "targetid,"+
            "similarity,"+
            "notmembercount,"+
            
            "result,"+
            "leftglovesconfidence,"+
            "rightglovesconfidence,"+
            "leftgloves,"+
            "rightgloves,"+
            
            "facecover,"+
            "facecoverconfidence,"+
            "headcover,"+
            "headcoverconfidence,"+
            "violation,"+
            
            "signinresult,"+
            "membernum)"+
            "values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (model['capture']['frameId'],
            datetime.utcfromtimestamp(int(model['capture']['timestamp'])+ 28800),
            model['signinValidate']['faceCount'],
            model['capture']['sourceImageUrl'],
            model['sourceImagePersonList'][i]['targetImageUrl'],
            
            model['signinValidate']['memberCount'],
            model['sourceImagePersonList'][i]['faceId'],
            model['sourceImagePersonList'][i]['targetId'],
            model['sourceImagePersonList'][i]['similarity'],
            model['signinValidate']['notMemberCount'],
            
            model['signinValidate']['ppeResult'],
            round(model['sourceImagePersonList'][i]['ppeDetection']['left_hand']['left_hand_cover_confidence'],2),
            round(model['sourceImagePersonList'][i]['ppeDetection']['right_hand']['right_hand_cover_confidence'],2),
            model['sourceImagePersonList'][i]['ppeDetection']['left_hand']['left_hand_cover'],
            model['sourceImagePersonList'][i]['ppeDetection']['right_hand']['right_hand_cover'],
            
            model['sourceImagePersonList'][i]['ppeDetection']['face']['face_cover'],
            round(model['sourceImagePersonList'][i]['ppeDetection']['face']['face_cover_confidence'],2),
            model['sourceImagePersonList'][i]['ppeDetection']['head']['head_cover'],
            round(model['sourceImagePersonList'][i]['ppeDetection']['head']['head_cover_confidence'],2),
            model['sourceImagePersonList'][i]['violation'],
            
            model['sourceImagePersonList'][i]['signinResult'],
            2
            ))
        conn.commit()
    def getResult(self):
        return self.__outputResult
