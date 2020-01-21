import paho.mqtt.client as mqtt
import sys
import time
import threading
import fins.udp
import PySimpleGUI as sg
import queue
import socket
import cv2


TCP_IP = '192.168.0.44'#192.168.0.34(dell/linux)#192.168.0.44(dell/old)
TCP_PORT = 5205
BUFFER_SIZE = 1024

broker = "mqtt.eclipse.org"
port = 1883
keepAlive = 60
topicL1 = "SetSystem/luzes/L1"
topicL2 = "SetSystem/luzes/L2"
topicCompState = "SetSystem/compressor/state"
topicCompPress = "SetSystem/compressor/press"
topicQ1 = "SetSystem/outlets/Q1"
topicQ2 = "SetSystem/outlets/Q2"
topicQ3 = "SetSystem/outlets/Q3"

L1CLPMem = "\x00\x0A\x00"
L2CLPMem = "\x00\x0A\x01"
CompCLPMem = "\x00\x0A\x02"
Q1CLPMem = "\x00\x0A\x05"
Q2CLPMem = "\x00\x64\x00"
Q3CLPMem = "\x00\x64\x00"
CLPReadTrigger = "\x00\x00\x00"

fins_instance = None
#mem_read = None
#mem_bit = None
yesCount = 0
noCount = 0
rememberNo = False
rememberYes = False
Auto = False
Manual = False
AskMode = False
RESET = False

read_q = queue.Queue()
write_q = queue.Queue()
cam_q = queue.Queue()

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)#IPV4,TCP
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) 
s.bind((TCP_IP, TCP_PORT))
s.listen(1)

def on_connect(client, userdata, flags, rc):
    print(f"Conectado com sucesso ao broker:{broker}.Codigo:{str(rc)}")
    client.subscribe(topicL1)
    client.subscribe(topicL2)
    client.subscribe(topicQ1)
    client.subscribe(topicQ2)
    client.subscribe(topicQ3)
    client.subscribe(topicCompState)
    #client.subscribe(topicCompPress)


def on_message(client, userdata, msg):
    data = str(msg.payload.decode('UTF-8'))
    print(f"Mensagem recebida.Topico:{msg.topic}.Mensagem:{data}")
    global fins_instance
    if msg.topic == topicL1:
        if data == "0":
            print("Desligando memória CLP")
            writeWorkBit(fins_instance,L1CLPMem,'\x00')
        elif data == "1":
            print("Ligando memória CLP")
            writeWorkBit(fins_instance,L1CLPMem,'\x01')
    elif msg.topic == topicL2:
        if data == "0":
            print("Desligando memória CLP")
            writeWorkBit(fins_instance,L2CLPMem,'\x00')
        elif data == "1":
            print("Ligando memória CLP")
            writeWorkBit(fins_instance,L2CLPMem,'\x01')
    elif msg.topic == topicQ1:
        if data == "0":
            print("Desligando memória CLP")
            writeWorkBit(fins_instance,Q1CLPMem,'\x00')
        elif data == "1":
            print("Ligando memória CLP")
            writeWorkBit(fins_instance,Q1CLPMem,'\x01')
    elif msg.topic == topicQ2:
        if data == "0":
            print("Desligando memória CLP")
            writeWorkBit(fins_instance,Q2CLPMem,'\x00')
        elif data == "1":
            print("Ligando memória CLP")
            writeWorkBit(fins_instance,Q2CLPMem,'\x01')
    elif msg.topic == topicQ3:
        if data == "0":
            print("Desligando memória CLP")
            writeWorkBit(fins_instance,Q3CLPMem,'\x00')
        elif data == "1":
            print("Ligando memória CLP")
            writeWorkBit(fins_instance,Q3CLPMem,'\x01')
    elif msg.topic == topicCompState:
        if data == "0":
            print("Desligando memória CLP")
            writeWorkBit(fins_instance,CompCLPMem,'\x00')
        elif data == "1":
            print("Ligando memória CLP")
            writeWorkBit(fins_instance,CompCLPMem,'\x01')

def mqttPublish(topic,payload):
    print(f"Publicando {payload} para {topic}")
    client.publish(topic,payload=payload,qos=1,retain=False)

def handleMQTT(i):
    print(f"handleMQTT running on Thread {i}")
    while True:
        client.on_connect = on_connect
        client.on_message = on_message

def readWorkBit(fins_instance,mem):
    mem_read = fins_instance.memory_area_read(fins.FinsPLCMemoryAreas().WORK_BIT,bytes(mem,'ascii'))
    mem_bit = str(mem_read)[-2:-1]
    print(f"CLP Read Result: {mem_read}")
    return mem_bit

def writeWorkBit(fins_instance,mem,data):
    fins_instance.memory_area_write(fins.FinsPLCMemoryAreas().WORK_BIT,bytes(mem,'ascii'),bytes(data,'ascii'),1)

def readWorkLoop(i,fins_instance):
    print(f"readWorkLoop running on Thread {i}")
    trigger = None
    while True:
        global L1CLPMem,topicL1,L2CLPMem,topicL2,Q1CLPMem,topicQ1,Q2CLPMem,topicQ2,Q3CLPMem,topicQ3,CompCLPMem,topicCompState
        mem_bit = readWorkBit(fins_instance,CLPReadTrigger)
        if mem_bit == "1":
            trigger = 1
        #handle trigger result
        elif trigger == 1:
            mem_bit = readWorkBit(fins_instance,L1CLPMem)
            time.sleep(0.15)
            mqttPublish(topicL1,mem_bit)
            time.sleep(0.15)
            mem_bit = readWorkBit(fins_instance,L2CLPMem)
            time.sleep(0.15)
            mqttPublish(topicL2,mem_bit)
            time.sleep(0.15)
            mem_bit = readWorkBit(fins_instance,Q1CLPMem)
            time.sleep(0.15)
            mqttPublish(topicQ1,mem_bit)
            time.sleep(0.15)
            mem_bit = readWorkBit(fins_instance,Q2CLPMem)
            time.sleep(0.15)
            mqttPublish(topicQ2,mem_bit)
            time.sleep(0.15)
            mem_bit = readWorkBit(fins_instance,Q3CLPMem)
            time.sleep(0.15)
            mqttPublish(topicQ3,mem_bit)
            time.sleep(0.15)
            mem_bit = readWorkBit(fins_instance,CompCLPMem)
            time.sleep(0.15)
            mqttPublish(topicCompState,mem_bit)
            time.sleep(0.15)
            trigger = 0
            #mem_read = None

def readSocket(read_q,write_q):
    while True:
        print(f"Sever listening to {TCP_IP}:{TCP_PORT}")
        connection,adress = s.accept()
        print(f"Connection from {adress} sucessful!")
        while True:
            data = connection.recv(BUFFER_SIZE)
            if not data:
                break
            msg = data.decode('utf-8')
            print(f"Received data:{msg}")
            read_q.put(msg)
            write_q.put(connection)
            
        connection.close()

def sendSocket(data,write_q):
    print("Sending data")
    conn = write_q.get()
    conn.sendall(data.encode('UTF-8'))
    print(f"Sent {data} to {conn}")

def camRead(cam_q):
    cap = cv2.VideoCapture(0)
    while True:
        ret, frame = cap.read()
        imgbytes=cv2.imencode('.png', frame)[1].tobytes()
        cam_q.put(imgbytes)

try:
    print("Inicializando MQTT")
    client = mqtt.Client()

    client.connect(broker, port, keepAlive)
    client.loop_start()
    t = threading.Thread(target=handleMQTT,args=(1,),daemon=True)
    t.start()

    fins_instance = fins.udp.UDPFinsConnection()
    fins_instance.connect('192.168.250.1')
    fins_instance.dest_node_add=1
    fins_instance.srce_node_add=25
    
    t2 = threading.Thread(target=readWorkLoop,args=(2,fins_instance),daemon=True)
    t2.start()

    modeButtons = [sg.Button("AUTO",key='_autoBtn_'),sg.Button("MANUAL",key='_manBtn_')]
    choiceButtons = [sg.Button("SIM",key='_yesBtn_'),sg.Button("NÃO",key='_noBtn_')]
    camImage = [sg.Image(filename='', key='-IMAGE-')]

    layout = [
        [sg.Text("Mensagens recebidas:",font=('Helvetica',17)),sg.Text('',font=('Helvetica',14),size=(20,1),key='_fromCobot_')],
        [sg.Text("Perguntas:",font=('Helvetica',17)),sg.Text('',font=('Helvetica',14),size=(60,1),key='_promptStr_')],
        [sg.Column([modeButtons], visible=False, key='modeCOL'),sg.Column([choiceButtons], visible=False, key='choiceCOL'),sg.Button("RESET",key='_RESET_',visible=True,button_color=('white','red'))],
        [sg.Text("Modo ativo:",font=('Helvetica',17)),sg.Text("",key='_modeStr_',font=('Helvetica',14),size=(10,1))],
        [sg.Column([camImage])],
        [sg.Exit(focus=True)]
    ]


    camThread = threading.Thread(target=camRead,args=(cam_q,),daemon=True)
    #camThread.start()

    readSocketThread = threading.Thread(target=readSocket,args=(read_q,write_q),daemon=True)
    readSocketThread.start()

    sg.SetOptions(auto_size_buttons=False)

    window = sg.Window('Cobot Control',layout)


    while True:  # Event Loop
        event, values = window.Read(timeout=100)
        #print(event, values)
        try:
            imgbytes = cam_q.get_nowait()
            window.Element('-IMAGE-').Update(data=imgbytes)
        except queue.Empty:
            pass
        if Auto or Manual:
            if Auto:
                window.Element('_modeStr_').Update("AUTO")
                window.Refresh()
            if Manual:
                window.Element('_modeStr_').Update("MANUAL")
                window.Refresh()
        else:
            window.Element('_modeStr_').Update("NONE")
            window.Refresh()

        if event in (None,'Exit'):
            break

        elif event == '_yesBtn_':
            print(event)
            yesCount+=1
            msg = "GoB|"
            sendSocketThread = threading.Thread(target=sendSocket,args=(msg,write_q),daemon=True)
            sendSocketThread.start()
            if yesCount >=3:
                if Auto:
                    rememberYes = True
                yesCount = 0
                noCount = 0
            elif noCount >=2:
                if Auto:
                    rememberNo = True
                noCount = 0
                yesCount = 0
            window.Element('_promptStr_').Update("")
            window.Element('choiceCOL').Update(visible=False)
            window.Refresh()

        elif event == '_noBtn_':
            print(event)
            noCount+=1
            msg = "GoHome|"
            sendSocketThread = threading.Thread(target=sendSocket,args=(msg,write_q),daemon=True)
            sendSocketThread.start() 
            if noCount >=3 or yesCount >=2:
                noCount = 0
                yesCount = 0           
            window.Element('_promptStr_').Update("")
            window.Element('choiceCOL').Update(visible=False)
            window.Refresh()

        elif event == '_manBtn_':
            print(event)
            if AskMode and Auto == False:
                msg = "Manual|"
                sendSocketThread = threading.Thread(target=sendSocket,args=(msg,write_q),daemon=True)
                sendSocketThread.start()
                Manual=True
                AskMode=False
            window.Element('_promptStr_').Update("")
            window.Element('modeCOL').Update(visible=False)
            window.Refresh()

        elif event == '_autoBtn_':
            print(event)
            if AskMode and Manual == False:
                msg = "Auto|"
                sendSocketThread = threading.Thread(target=sendSocket,args=(msg,write_q),daemon=True)
                sendSocketThread.start()
                Auto=True
                AskMode=False
            window.Element('_promptStr_').Update("")
            window.Element('modeCOL').Update(visible=False)
            window.Refresh()

        
        elif event == '_RESET_':
            print(event)
            Auto = False
            Manual = False
            yesCount = 0
            noCount = 0
            rememberYes = False
            rememberNo = False
            RESET = True
            window.Element('_promptStr_').Update("RESET")
            window.Refresh()
        
        while True:
            try:
                msg = read_q.get_nowait()
            except queue.Empty:
                break
            if msg:
                window.Element('_fromCobot_').Update(msg)
                window.Refresh()
                if msg == "GetReset" and RESET:
                    msg = "RESET|"
                    sendSocketThread = threading.Thread(target=sendSocket,args=(msg,write_q),daemon=True)
                    sendSocketThread.start()
                    RESET = False

                if msg == "AskMode":
                    window.Element('_promptStr_').Update("Favor selecionar o modo de operação:")
                    window.Element('modeCOL').Update(visible=True)
                    window.Refresh()
                    AskMode=True

                if msg == "FailA":
                    if rememberYes == False and rememberNo == False:
                        window.Element('choiceCOL').Update(visible=True)
                        window.Refresh()
                        if yesCount >=2 or noCount >=2 and Auto:
                            window.Element('_promptStr_').Update("A não encontrado,deseja repetir a ação anterior sempre?")
                            window.Refresh()
                        else:
                            window.Element('_promptStr_').Update("A não encontrado,montar B?")
                            window.Refresh()
                    elif rememberYes == True or rememberNo == True:
                        if rememberYes:
                            window.Element('_promptStr_').Update("A não encontrado,segindo para B")
                            window.Refresh()
                            msg = "GoB|"
                            sendSocketThread = threading.Thread(target=sendSocket,args=(msg,write_q),daemon=True)
                            sendSocketThread.start()
                        elif rememberNo:
                            window.Element('_promptStr_').Update("A não encontrado,retornando a HOME")
                            window.Refresh()
                            msg = "GoHome|"
                            sendSocketThread = threading.Thread(target=sendSocket,args=(msg,write_q),daemon=True)
                            sendSocketThread.start()
    window.Close()
        

except KeyboardInterrupt:
    print("Programa cancelado")
    sys.exit(0)
