from merge import MergeResult

def lambda_handler(event, context):
    dataModel = event
    mergeResult = MergeResult(dataModel)
    mergeResult.merge_ppe_faceValidation()
    mergeResult.redshiftInject()
    
    
    return mergeResult.getResult()