import config
import psycopg2
from datetime import datetime

from linebot import LineBotApi
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import TemplateSendMessage, CarouselTemplate, CarouselColumn, PostbackAction, TextSendMessage


class SourceColumn():
    def __init__(self, dataModel):
        self.imageUrl = dataModel['capture']['sourceImageUrl']
        self.imageCaptureTime = datetime.fromtimestamp(int(dataModel['capture']['timestamp'] + 28800))
        
class MemberColumns():
    def __init__(self, dataModel):
        self.matchedFaceList = dataModel['sourceImageMemberList']

class MatchedFacesMessage():
    def __init__(self, sourceColumn, memberColumns):
        self.__sourceColumn = sourceColumn
        self.__memberColumns = memberColumns
     
    def __getSourceCarouselColumn(self):
        sourceCarouselColumn = CarouselColumn(
                                    thumbnail_image_url=self.__sourceColumn.imageUrl,
                                    title='來源影像',
                                    text='時間：{}'.format(self.__sourceColumn.imageCaptureTime),
                                    actions=[
                                        PostbackAction(
                                            label=' ',
                                            data='doNothing'
                                        )
                                    ]
                                )
        
        return sourceCarouselColumn
    
    def __getMemberCarouselColumns(self):
        memberCarouselColumns = []
        
        for memberFace in self.__memberColumns.matchedFaceList:
            carouselColumn = CarouselColumn(
                thumbnail_image_url=memberFace['targetImageUrl'],
                title='成員影像',
                text='相似度：{}%'.format(round(memberFace['similarity'], 2)),
                actions=[
                    PostbackAction(
                        label=' ',
                        data='doNothing'
                    )
                ]
            )
            
            memberCarouselColumns.append(carouselColumn)
        
        return memberCarouselColumns
    
    def getCarouselTemplate(self):
        sourceCarouselColumn = self.__getSourceCarouselColumn()
        memberCarouselColumns = self.__getMemberCarouselColumns()
        carouselTemplate = TemplateSendMessage(
                                alt_text='收到通報訊息！',
                                template=CarouselTemplate(
                                    columns=[sourceCarouselColumn] + memberCarouselColumns
                                )
                            )
        
        return carouselTemplate
        
class ValidationResultMessage():
    def __init__(self, dataModel):
        self.__personCount = dataModel['signinValidate']['faceCount']
        self.__memberCount = dataModel['signinValidate']['memberCount']
        self.__passedPersonCount = dataModel['signinValidate']['validPpeCount']
        self.__signInPersonCount = dataModel['signinValidate']['validSigninCount']
        self.__imageCaptureTime = datetime.fromtimestamp(int(dataModel['capture']['timestamp'] + 28800))
        self.__personList = dataModel['sourceImagePersonList']
        self.text = None
    
    def __getPersonTotalCount(self, faceId, item):
        conn = psycopg2.connect(
                    dbname=config.dbName,
                    host=config.hostName,
                    port=config.port,
                    user=config.dbUserName,
                    password=config.dbPassword
                )
        cur = conn.cursor()
        
        if (item == 'signin'):
            cur.execute("SELECT * FROM ppe_analytics where faceid= \'{}\' and  violation=\'False\'".format(faceId))
        
        else:
            cur.execute("SELECT * FROM ppe_analytics where faceid= \'{0}\' and  {1}=\'False\'".format(faceId, item))
        
        return len(cur.fetchall())
    
    def __getPersonListText(self):
        personListText = ''
        for index, person in enumerate(self.__personList, start=1):
            signInResult = (lambda person: '成功' if person['validSignin'] else '失敗')(person)
            validMemberResult = (lambda person: '合格' if person['isMember'] else '不合格')(person)
            faceConfidence = round(person['faceConfidence'], 2)
            faceCoordinate = {
                                'X': round(person['faceCoordinate']['X'], 2), 
                                'Y': round(person['faceCoordinate']['Y'], 2)
                             }
                             
            
            validMaskResult = (lambda person: '合格' if person['ppeDetection']['face']['face_cover'] else '不合格')(person)
            maskConfidence = round(person['ppeDetection']['face']['face_cover_confidence'], 2)
            
            validHelmetResult = (lambda person: '合格' if person['ppeDetection']['head']['head_cover'] else '不合格')(person)
            helmetConfidence = round(person['ppeDetection']['head']['head_cover_confidence'], 2)
            
            validLeftGloveResult = (lambda person: '合格' if person['ppeDetection']['left_hand']['left_hand_cover'] else '不合格')(person)
            leftGloveConfidence = round(person['ppeDetection']['left_hand']['left_hand_cover_confidence'], 2)
            
            validRightGloveResult = (lambda person: '合格' if person['ppeDetection']['right_hand']['right_hand_cover'] else '不合格')(person)
            rightGloveConfidence = round(person['ppeDetection']['right_hand']['right_hand_cover_confidence'], 2)
            
            if (person['isMember'] == True):
                similarity = round(person['similarity'], 2)
                signInCount = self.__getPersonTotalCount(faceId=person['faceId'], item='signin')
                
                maskViolationCount = self.__getPersonTotalCount(faceId=person['faceId'], item='facecover')
                helmetViolationCount = self.__getPersonTotalCount(faceId=person['faceId'], item='headcover')
                leftGloveViolationCount  = self.__getPersonTotalCount(faceId=person['faceId'], item='leftgloves')
                rightGloveViolationCount = self.__getPersonTotalCount(faceId=person['faceId'], item='rightgloves')
                
                personListText += '人員【{0}】：\n' \
                                '\t\t簽到：{1}\n' \
                                '\t\t成員查驗：{2}\n' \
                                '\t\t\t\t信心指數：{3}%\n' \
                                '\t\t\t\t相似度：{4}%\n' \
                                '\t\t\t\t位置：({5[X]}, {5[Y]})\n' \
                                '\t\t\t\t已簽到{6}次\n' \
                                '\t\t(1)口罩查驗：{7}\n' \
                                '\t\t\t\t\t信心指數：{8}%\n' \
                                '\t\t\t\t\t已違規{9}次\n'\
                                '\t\t(2)安全帽查驗：{10}\n' \
                                '\t\t\t\t\t信心指數：{11}%\n' \
                                '\t\t\t\t\t已違規{12}次\n'\
                                '\t\t(3)右手套查驗：{13}\n' \
                                '\t\t\t\t\t信心指數：{14}%\n' \
                                '\t\t\t\t\t已違規{15}次\n'\
                                '\t\t(4)左手套查驗：{16}\n' \
                                '\t\t\t\t\t信心指數：{17}%\n' \
                                '\t\t\t\t\t已違規{18}次\n\n'.format(
                                                                index,
                                                                signInResult,
                                                                validMemberResult,
                                                                faceConfidence,
                                                                similarity,
                                                                faceCoordinate,
                                                                signInCount,
                                                                validMaskResult,
                                                                maskConfidence,
                                                                maskViolationCount,
                                                                validHelmetResult,
                                                                helmetConfidence,
                                                                helmetViolationCount,
                                                                validLeftGloveResult,
                                                                leftGloveConfidence,
                                                                leftGloveViolationCount,
                                                                validRightGloveResult,
                                                                rightGloveConfidence,
                                                                rightGloveViolationCount
                                                            )
            
            else:
                personListText += '人員【{0}】：\n' \
                                '\t\t簽到：{1}\n' \
                                '\t\t成員查驗：{2}\n' \
                                '\t\t\t\t信心指數：{3}%\n' \
                                '\t\t\t\t位置：({4[X]}, {4[Y]})\n' \
                                '\t\t(1)口罩查驗：{5}\n' \
                                '\t\t\t\t\t信心指數：{6}%\n' \
                                '\t\t(2)安全帽查驗：{7}\n' \
                                '\t\t\t\t\t信心指數：{8}%\n' \
                                '\t\t(3)右手套查驗：{9}\n' \
                                '\t\t\t\t\t信心指數：{10}%\n' \
                                '\t\t(4)左手套查驗：{11}\n' \
                                '\t\t\t\t\t信心指數：{12}%\n\n'.format(
                                                                    index,
                                                                    signInResult,
                                                                    validMemberResult,
                                                                    faceConfidence,
                                                                    faceCoordinate,
                                                                    validMaskResult,
                                                                    maskConfidence,
                                                                    validHelmetResult,
                                                                    helmetConfidence,
                                                                    validLeftGloveResult,
                                                                    leftGloveConfidence,
                                                                    validRightGloveResult,
                                                                    rightGloveConfidence
                                                                )
            
        return personListText
    
    def getTextTemplate(self):
        personListText = self.__getPersonListText()
        self.text = '警示通報\n\n' \
                    '來源人數：{0}\n' \
                    '成員人數：{1}\n' \
                    '合格人數：{2}\n' \
                    '簽到人數：{3}\n' \
                    '時間：{4}\n\n' \
                    '{5}'.format(self.__personCount, self.__memberCount , self.__passedPersonCount, self.__signInPersonCount, self.__imageCaptureTime, personListText)
        
        textTemplate = TextSendMessage(text=self.text)
        
        return textTemplate

class AlertNotify():
    def __init__(self, matchedFacesMessage, validationResultMessage):
        self.__receiverLineId = config.receiverLineId
        self.__matchedFacesMessage = matchedFacesMessage
        self.__validationResultMessage = validationResultMessage
     
    def pushMessages(self):
        matchedFacesTemplateMessage = self.__matchedFacesMessage.getCarouselTemplate()
        validationResulTemplateMessage = self.__validationResultMessage.getTextTemplate()
        
        lineBotApi = LineBotApi(config.channelAccessToken)
        
        try:
            lineBotApi.push_message(self.__receiverLineId, [matchedFacesTemplateMessage, validationResulTemplateMessage])
            pushResult = 'Success'
            
        except LineBotApiError as e:
            pushResult = 'LineBotApiError: {}'.format(e.error.message)
        
        return pushResult