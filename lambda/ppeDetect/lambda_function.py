from ppeDetect import PpeDetection
import config

def lambda_handler(event, context):
    dataModel = event
    ppeDetection = PpeDetection(dataModel, config.aws_access_key_id, config.aws_secret_access_key, config.region_name)
    ppeDetection.ppeDetect()
    ppeDetectionModel = ppeDetection.getModel()
    
    return ppeDetectionModel