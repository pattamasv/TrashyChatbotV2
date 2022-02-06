from fastai.vision import *
from flask import Flask, request, abort, render_template
from flask_sqlalchemy import SQLAlchemy
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import *
from linebot.models.responses import Content
from linebot.models.messages import*
from linebot.models.template import *
from pyngrok import conf, ngrok
from PIL import Image, ImageFile
from geopy.distance import *
import io
import json,requests
import geopy.distance as ps
import pandas as pd
import numpy as np
from models import db,Users
import time

path = Path()
learn = load_learner(path, 'export.pkl')
print('model loaded!')

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

@app.before_first_request
def create_table():
    db.create_all()

ImageFile.LOAD_TRUNCATED_IMAGES = True

channelAccessToken = "+7Mf5GuIW9Ow1Zzmhttoyj1iUuQAK18D7HhFC4ko4br/+xiQRygsRM7TOsNdqWcHfKR2ouDa/leN2VXxyuTzbTY4NUyTY5EfnX4tMRmNMWRO/5/Muz3zQs+izRy8PwG36kfXaXlCafUjKFHzrKkv1QdB04t89/1O/w1cDnyilFU="
channelSecret = "cc8ba602cc5c9ec41feb99ae38b846ea"

CONFIDENCE_THRESHOLD = 70
PIXEL_RESIZE_TO = 256

line_bot_api = LineBotApi(channelAccessToken)
handler = WebhookHandler(channelSecret)

wongpanit = pd.read_excel('wongpanit.xlsx')
refunex = pd.read_excel('Refun Machine Location.xlsx')
price = pd.read_excel('predicted_result.xlsx')
price.rename(columns={'Unnamed: 4':'โลหะ','Unnamed: 1':'กระดาษ','Unnamed: 2':'แก้ว','Unnamed: 3':'พลาสติก'},inplace=True)

@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    print("# Webhook event:\n", body)
    print('-'*100)

    app.logger.info("Request body: " + body)

    try:
         handler.handle(body ,signature)
    except InvalidSignatureError:
         abort(400)
    
    return 'OK'

@app.route('/')
def main():
    users = Users.query.all()
    return render_template('index.html', users=users)

@handler.add(PostbackEvent)
def handle_post(event:PostbackEvent)-> None : # echo function 
      data  = event.postback.data
      #d = json.loads(data1)
      #data1 = data[80:87]
      data1 =eval(data)
    
      lat = data1[0]['latitude']
      lng = data1[0]['longitude']
      if  data1[1]['trashtype']=='plastic':
          ptype = 'ตู้รีฟัน'
          result = handle_location(lat,lng,refunex,1)
      else:
          ptype = 'วงษ์พาณิชย์'
          result = handle_location(lat,lng,wongpanit,1)
      print(result)
      #TextSendMessage(text=lat+' '+lng+' '+data1)
      line_bot_api.reply_message(event.reply_token, [TextSendMessage(
                            text= result)])

      return data1

@handler.add(MessageEvent, message=(LocationMessage,ImageMessage,TextMessage))
def handle_message(event: MessageEvent)-> None : # echo function
        #Text
        greeting = ['สวัสดีค่ะ','สวัสดีครับ','สวัสดี','ตู้รีฟัน']
        end = ['ขอบคุณ','ขอบคุณค่ะ','ขอบคุณครับ','เอาไว้ก่อน','ยังไม่ต้องการขาย']
        yes = ['ต้องการขาย','พิกัดใกล้ฉัน','ต้องการสะสมแต้มหรือขาย']
        trashtype = ['ขยะรีไซเคิล', 'ขยะทั่วไป', 'ขยะอันตราย', 'ขยะเปียก']
        recycle = ['แก้ว', 'โลหะ', 'พลาสติก', 'กระดาษ']
        destrash = ['ขยะแต่ละประเภท']
        #no = ['เอาไว้ก่อน','ยังไม่ต้องการขาย']
      
        if isinstance(event.message, TextMessage):
            for g in greeting:
                if (g == event.message.text ):
                    t = 'สวัสดีค่ะ ขยะของคุณคือประเภทอะไร?'
                    t1 = 'ขยะทั่วไป เช่น ซองขนม ถุงพลาสติก โฟมใส่อาหาร'
                    t2 = 'ขยะรีไซเคิล เช่น พลาสติก กระดาษ โลหะ แก้ว'
                    t3 = 'ขยะอันตราย เช่น ของมีคม แบตเตอรี่ หลอดไฟ ขยะติดเชื้อ'
                    t4 = 'ขยะเปียก เช่น เศษอาหาร พืชผัก เปลือกผลไม้'
                    res = [TextSendMessage(text = t), TextSendMessage(text = t1 + '\n' + t2 + '\n' + t3 + '\n' + t4,
                            quick_reply=QuickReply(
                                items=[
                                    QuickReplyButton(action=MessageAction(label="ขยะแต่ละประเภท", text="ขยะแต่ละประเภท")),
                                    QuickReplyButton(action=MessageAction(label="พิกัดใกล้ฉัน", text="พิกัดใกล้ฉัน")),   
                                    QuickReplyButton(action=LocationAction(label="ส่งตำแหน่ง"))
                               ]))]        
                    line_bot_api.reply_message(event.reply_token,res)  
                    break  
            
            for d in destrash:
                if (d == event.message.text ):
                    t1 = 'ขยะทั่วไป เช่น ซองขนม ถุงพลาสติก โฟมใส่อาหาร'
                    t2 = 'ขยะรีไซเคิล เช่น พลาสติก กระดาษ โลหะ แก้ว'
                    t3 = 'ขยะอันตราย เช่น ของมีคม แบตเตอรี่ หลอดไฟ ขยะติดเชื้อ'
                    t4 = 'ขยะเปียก เช่น เศษอาหาร พืชผัก เปลือกผลไม้'
                    res = [TextSendMessage(text = t1 + '\n' + t2 + '\n' + t3 + '\n' + t4,
                            quick_reply=QuickReply(
                                items=[
                                    QuickReplyButton(action=MessageAction(label="ขยะแต่ละประเภท", text="ขยะแต่ละประเภท")),
                                    QuickReplyButton(action=MessageAction(label="พิกัดใกล้ฉัน", text="พิกัดใกล้ฉัน")),   
                                    QuickReplyButton(action=LocationAction(label="ส่งตำแหน่ง"))
                               ]))]        
                    line_bot_api.reply_message(event.reply_token,res)        
                    break  

            for t in trashtype:
                if (t == event.message.text ):
                  if event.message.text == 'ขยะรีไซเคิล':
                    res = [TextSendMessage(
                            text='ขยะรีไซเคิลประเภทไหน? แก้ว กระดาษ โลหะ หรือพลาสติก',
                            quick_reply=QuickReply(
                                items=[
                                    QuickReplyButton(action=MessageAction(label="แก้ว", text="แก้ว")),
                                    QuickReplyButton(action=MessageAction(label="กระดาษ", text="กระดาษ")),   
                                    QuickReplyButton(action=MessageAction(label="โลหะ", text="โลหะ")),
                                    QuickReplyButton(action=MessageAction(label="พลาสติก", text="พลาสติก"))
                               ]))]        
                    line_bot_api.reply_message(event.reply_token,res)
                    break

                  elif event.message.text == 'ขยะเปียก':
                      bin = 'ถังขยะสีเขียว'
                      url = 'https://www.img.in.th/images/bc79d41e1beeab5cdb0c88f0f6a24678.jpg'
                      app.logger.info("url=" + url)
                      reply1 = 'ประเภทขยะของคุณคือ %s ควรทิ้งใน%s'%(event.message.text,bin)
                      res = [TextSendMessage(text=reply1), ImageSendMessage(url, url,
                                quick_reply=QuickReply(
                                    items=[
                                        QuickReplyButton(action=MessageAction(label="ขยะแต่ละประเภท", text="ขยะแต่ละประเภท")),
                                        QuickReplyButton(action=MessageAction(label="พิกัดใกล้ฉัน", text="พิกัดใกล้ฉัน")),
                                        QuickReplyButton(action=LocationAction(label="ส่งตำแหน่ง"))
                                    ]))]
                      line_bot_api.reply_message(event.reply_token,res) 
                      break

                  elif event.message.text == 'ขยะทั่วไป':
                      bin = 'ถังขยะสีน้ำเงิน'
                      url = 'https://www.img.in.th/images/d0edc27448de8591252bfeee4392ccd2.jpg'
                      app.logger.info("url=" + url)
                      reply1 = 'ประเภทขยะของคุณคือ %s ควรทิ้งใน%s'%(event.message.text,bin)
                      res = [TextSendMessage(text=reply1), ImageSendMessage(url, url,
                                  quick_reply=QuickReply(
                                      items=[
                                          QuickReplyButton(action=MessageAction(label="ขยะแต่ละประเภท", text="ขยะแต่ละประเภท")),                                          
                                          QuickReplyButton(action=MessageAction(label="พิกัดใกล้ฉัน", text="พิกัดใกล้ฉัน")),
                                          QuickReplyButton(action=LocationAction(label="ส่งตำแหน่ง"))
                                      ]))]
                      line_bot_api.reply_message(event.reply_token,res)
                      break

                  elif event.message.text == 'ขยะอันตราย':
                      bin = 'ถังขยะสีแดง'
                      url = 'https://www.img.in.th/images/4fe2a116e8323985bd4a86ace49ddd07.jpg'
                      app.logger.info("url=" + url)
                      reply1 = 'ประเภทขยะของคุณคือ %s ควรทิ้งใน%s'%(event.message.text,bin)
                      res = [TextSendMessage(text=reply1), ImageSendMessage(url, url,
                                  quick_reply=QuickReply(
                                      items=[
                                          QuickReplyButton(action=MessageAction(label="ขยะแต่ละประเภท", text="ขยะแต่ละประเภท")),
                                          QuickReplyButton(action=MessageAction(label="พิกัดใกล้ฉัน", text="พิกัดใกล้ฉัน")),
                                          QuickReplyButton(action=LocationAction(label="ส่งตำแหน่ง")),
                                      ]))]
                      line_bot_api.reply_message(event.reply_token,res) 
                      break
                  break
            for r in recycle:
              if (r == event.message.text):
                if event.message.text == 'พลาสติก':
                  bin = 'ถังขยะสีเหลือง'
                  url = 'https://www.img.in.th/images/6d4320aa5180bb8960d0d520a58d25b7.jpg'
                  app.logger.info("url=" + url)
                  predictprice = getprice(price,r)

                  reply1 = 'ประเภทขยะของคุณคือ %s ควรทิ้งใน%s'%(event.message.text,bin)
                  reply2 = 'หรือคุณสามารถนำไปสะสมแต้มได้ที่ตู้รีฟันเพื่อแลกของรางวัล หรือนำไปขายได้ที่วงษ์พาณิชย์'
                  confirm_template = ConfirmTemplate(text=predictprice+' ' +'ต้องการสะสมแต้มหรือขายไหม?', actions=[
                      MessageAction(label='ใช่', text='ต้องการสะสมแต้มหรือขาย'),
                      MessageAction(label='ไม่', text='เอาไว้ก่อน')
                  ])
                  res = [TextSendMessage(text=reply1), ImageSendMessage(url, url), TextSendMessage(text=reply2) ,TemplateSendMessage(alt_text='Confirm alt text', template=confirm_template,
                          quick_reply=QuickReply(
                              items=[
                                  QuickReplyButton(action=MessageAction(label="ขยะแต่ละประเภท", text="ขยะแต่ละประเภท")),
                                  QuickReplyButton(action=MessageAction(label="พิกัดใกล้ฉัน", text="พิกัดใกล้ฉัน")),   
                                  QuickReplyButton(action=LocationAction(label="ส่งตำแหน่ง"))
                              ]))]
                  line_bot_api.reply_message(event.reply_token,res)
                  break
                else:
                  bin = 'ถังขยะสีเหลือง'
                  url = 'https://www.img.in.th/images/6d4320aa5180bb8960d0d520a58d25b7.jpg'
                  app.logger.info("url=" + url)
                  predictprice = getprice(price,r)
                  reply1 = 'ประเภทขยะของคุณคือ %s ควรทิ้งใน%s'%(event.message.text,bin)
                  reply2 = 'หรือคุณสามารถนำไปขายได้ที่วงษ์พาณิชย์'
                  confirm_template = ConfirmTemplate(text=predictprice+' ' +'ต้องการขายไหม?', actions=[
                      MessageAction(label='ใช่', text='ต้องการขาย'),
                      MessageAction(label='ไม่', text='เอาไว้ก่อน'),
                  ])
                      
                  res = [TextSendMessage(text=reply1), ImageSendMessage(url, url),TextSendMessage(text=reply2), TemplateSendMessage(alt_text='Confirm alt text', template=confirm_template,
                          quick_reply=QuickReply(
                              items=[
                                  QuickReplyButton(action=MessageAction(label="ขยะแต่ละประเภท", text="ขยะแต่ละประเภท")),
                                  QuickReplyButton(action=MessageAction(label="พิกัดใกล้ฉัน", text="พิกัดใกล้ฉัน")),
                                  QuickReplyButton(action=LocationAction(label="ส่งตำแหน่ง"))
                              ]))]
                  line_bot_api.reply_message(event.reply_token,res) 
                  break

            for y in yes:
                if (y == event.message.text ):
                    #reply_message = 'หากต้องการขายสามารถส่งโลเคชั่นมาที่แชทเพื่อให้เราแนะนำวงษ์พาณิชย์สาขาที่ใกล้กับคุณ'
                    line_bot_api.reply_message(event.reply_token, [TextSendMessage( text='โปรดส่งโลเคชันมาที่แชทเพื่อให้เราแนะนำพิกัดที่ใกล้กับคุณ',
                            quick_reply=QuickReply(
                                items=[
                                    QuickReplyButton(action=MessageAction(label="ขยะแต่ละประเภท", text="ขยะแต่ละประเภท")),
                                    QuickReplyButton(action=MessageAction(label="พิกัดใกล้ฉัน", text="พิกัดใกล้ฉัน")),
                                    QuickReplyButton(action=LocationAction(label="ส่งตำแหน่ง"))
                                ]))])      
                    break

            for e in end:
                if (e == event.message.text ):
                    reply_message = 'Trashy Chatbot ยินดีให้บริการค่ะ ขอบคุณค่ะ'
                    line_bot_api.reply_message(event.reply_token, [TextSendMessage(text=reply_message)])
                    break
        
        #Image
        if isinstance(event.message, ImageMessage):
            image = download_and_resize_image(event,PIXEL_RESIZE_TO)
            data = open_image(image)
            data = data.resize((3,384,512))        
            predicted_class, predicted_index, outputs = learn.predict(data)
            
            reply_message = str(predicted_class)
            print(reply_message)
            print(str(outputs))

            profile = line_bot_api.get_profile(event.source.user_id)

            named_tuple = time.localtime() # get struct_time
            time_string = time.strftime("%d/%m/%Y, %H:%M:%S", named_tuple)

            userid = profile.user_id
            displayname = profile.display_name
            pictureurl = profile.picture_url
            timestamp = time_string
                    
            user = Users(userid=userid, displayname=displayname, pictureurl=pictureurl, trash=reply_message, timestamp=timestamp)
            db.session.add(user)
            db.session.commit()

            if reply_message == 'glass':
                trashtype = 'แก้ว'
                prob = float('%.2f' %(outputs[2]*100))
            elif reply_message == 'paper':
                trashtype = 'กระดาษ'
                prob = float('%.2f' %(outputs[4]*100))
            elif reply_message == 'metal':
                trashtype = 'โลหะ'
                prob = float('%.2f' %(outputs[3]*100))
            elif reply_message == 'plastic':
                trashtype = 'พลาสติก'
                prob = float('%.2f' %(outputs[5]*100))
            elif reply_message == 'trash':
                trashtype = 'ขยะทั่วไป'
                prob = float('%.2f' %(outputs[6]*100))
            elif reply_message == 'biological':
                trashtype = 'ขยะเปียก'
                prob = float('%.2f' %(outputs[0]*100))
            elif reply_message == 'dangerous':
                trashtype = 'ขยะอันตราย'
                prob = float('%.2f' %(outputs[1]*100))
            else:
                #trashtype = 'อื่นๆ'
                pass
            
            reply1 = 'ได้รับรูปขยะเรียบร้อยแล้ว ขยะของคุณคือ %s'%(trashtype)
            res =  [TextSendMessage(text=reply1,
                            quick_reply=QuickReply(
                                items=[
                                    QuickReplyButton(action=MessageAction(label="ขยะแต่ละประเภท", text="ขยะแต่ละประเภท")),
                                    QuickReplyButton(action=MessageAction(label="พิกัดใกล้ฉัน", text="พิกัดใกล้ฉัน")),
                                    QuickReplyButton(action=LocationAction(label="ส่งตำแหน่ง"))
                                ]))]      
            line_bot_api.reply_message(event.reply_token,res)

        #Location
        if isinstance(event.message, LocationMessage):
            lat = event.message.latitude
            lng = event.message.longitude
            plastic = {"trashtype":'plastic'}
            notplastic = {"trashtype":'notplastic'}
            prog_dict = {"latitude": lat,"longitude": lng}
            prog_string = json.dumps(prog_dict)
            prog_string1 = json.dumps(plastic)
            prog_string2 = json.dumps(notplastic)
            confirm_template = ConfirmTemplate(text='ต้องการพิกัดวงษ์พาณิชย์หรือตู้รีฟัน?', actions=[
                         PostbackAction(
                            label='วงษ์พาณิชย์',
                            text='วงษ์พาณิชย์',
                            data=(prog_string+','+prog_string2)
                        ),
                        #MessageAction(label='ตู้รีฟัน', text='ตู้รีฟัน'),
                        PostbackAction(
                            label='ตู้รีฟัน',
                            display_text='ตู้รีฟัน',
                            data=(prog_string+','+prog_string1)
                        ),
                    ])
            #txtresult = handle_location(lat,lng,3)
            #txtresult = handle_location(lat,lng,wongpanit,1)
            #refunresult = handle_location(lat,lng,refunex,1)
            #TextSendMessage(text='ร้านวงษ์พาณิชย์\n' + txtresult), TextSendMessage(text='ตู้รีฟัน\n' + refunresult),
            replyObj = [TemplateSendMessage(alt_text='Confirm alt text', template=confirm_template,
                            quick_reply=QuickReply(
                                items=[
                                    QuickReplyButton(action=MessageAction(label="ขยะแต่ละประเภท", text="ขยะแต่ละประเภท")),
                                    QuickReplyButton(action=MessageAction(label="พิกัดใกล้ฉัน", text="พิกัดใกล้ฉัน")),
                                    QuickReplyButton(action=LocationAction(label="ส่งตำแหน่ง"))
                                ]))]
            try:
                line_bot_api.reply_message(event.reply_token, replyObj)
            except LineBotApiError as e:
                    if e.message == 'Invalid reply token':
                        app.log.error(f'Failed to reply message: {event}')
                    else:
                        raise

#DownloadImage
def download_and_resize_image(event: MessageEvent, PIXEL_RESIZE_TO) -> bytes:
    src_image = io.BytesIO()
    message_content: Content = line_bot_api.get_message_content(event.message.id)

    for chunk in message_content.iter_content():
        src_image.write(chunk)

    with Image.open(src_image) as img:
        width, height = img.size
        if width < PIXEL_RESIZE_TO and height < PIXEL_RESIZE_TO:
            return src_image.getvalue()

        dst_image = io.BytesIO()
        img.thumbnail((PIXEL_RESIZE_TO, PIXEL_RESIZE_TO))
        img.save(dst_image, format=img.format)

    return dst_image

#ResponseLocationFromExcel
def handle_location(lat,lng,cdat,topK):
    result = getdistance(lat, lng,cdat)
    result = result.sort_values(by='km')
    result = result.iloc[0:topK]
    txtResult = ''
    for i in range(len(result)):
        nameshop = str(result.iloc[i]['Name'])
        kmdistance = '%.1f'%(result.iloc[i]['km'])
        newssource = str(result.iloc[i]['News_Source'])
        txtResult = txtResult + '%s อยู่ห่างจากคุณ %s กิโลเมตร\n%s\n\n'%(nameshop,kmdistance,newssource)
    return txtResult[0:-2]

def getdistance(latitude, longitude,cdat):
    coords_1 = (float(latitude), float(longitude))
    ## create list of all reference locations from a pandas DataFrame
    latlngList = cdat[['Latitude','Longitude']].values
    ## loop and calculate distance in KM using geopy.distance library and append to distance list
    kmsumList = []
    for latlng in latlngList:
      coords_2 = (float(latlng[0]),float(latlng[1]))
      kmsumList.append(ps.vincenty(coords_1, coords_2).km)
    cdat['km'] = kmsumList
    return cdat


def getprice(price,trashtype):
    result = pricecal(price,trashtype)
    if result > 0:
      reply = 'ขณะนี้ราคากำลังขึ้น'
    elif result < 0:
      reply = 'ขณะนี้ราคากำลังลง'
    elif result == 0:
      reply = 'ขณะนี้ราคากำลังนิ่ง'
    else:
      pass
    return reply 

def pricecal(price,trashtype):
    data = price['%s'%trashtype].values
    price = (data[0]-data[6])/data[6]
    return price
  
#ngrok
def log_event_callback(log):
  print(str(log))

# Open a HTTP tunnel on the port 5000
# <NgrokTunnel: "http://<public_sub>.ngrok.io" -> "http://localhost:5000">
http_tunnel = ngrok.connect(5000)
print(http_tunnel)

#SetWebHookLine
def setWebhook(endpoint,CHANNEL_ACCESS_TOKEN):
  endpointFixed = "https://" + endpoint.split('//')[-1] + '/callback'
  url = "https://api.line.me/v2/bot/channel/webhook/endpoint"
  header = {'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + CHANNEL_ACCESS_TOKEN}
  body = json.dumps({'endpoint': endpointFixed})
  response = requests.put(url=url, data=body, headers=header)
  print(response)
  obj = json.loads(response.text)
  print(obj)

setWebhook(http_tunnel.public_url, channelAccessToken)

conf.get_default().log_event_callback = log_event_callback

if __name__ == '__main__':
    app.run()