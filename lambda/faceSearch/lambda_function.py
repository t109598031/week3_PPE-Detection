from faceSearch import FaceSearch
from faceId import memberUrlList, memberIdList
import config

def lambda_handler(event, context):
    dataModel = event
    faceSearch = FaceSearch(dataModel, config.aws_access_key_id, config.aws_secret_access_key, config.region_name, config.collection_id)
    faceSearch.faceValidate(memberUrlList, memberIdList)
    
    return faceSearch.getModel()