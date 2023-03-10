import serial
from struct import pack, unpack
from serial.tools import list_ports
import time
import queue
import time
import multiprocessing

class Packet:
    def __init__(self, message_type: int, message: str) -> None:
        self.start = 0x69
        self.message_type = message_type
        self.message_lengh = len(message) % 256
        self.crc = (sum([ord(c) for c in message]) + len(message)) % 256
        self.message = message

    def get_packet(self) -> bytearray:
        header = pack(
            f"BBBB",
            self.start,
            self.message_type,
            self.message_lengh,
            self.crc,
        )
        return header + self.message.encode("ascii")

def code_decode(packet):
    return bytes([byte ^ 0x69 for byte in packet])

class dePacket:
    def __init__(self, callback, encrypted=False):
        self.encrypted = encrypted
        self.start = 0
        self.message_type = 0
        self.message_lenght = 0
        self.crc = 0
        self.payload = []
        self.deserializer_state = 0
        self.callback = callback
    # waiting_for_start = 0,
    #     waiting_for_type = 1,
    #     waiting_for_len = 2,
    #     waiting_for_crc = 3,
    #     data_acquisition = 4
    def deserialize(self, data):
        for i in range(len(data)):  
            # tmp = data[i]
            s = self.deserializer_state
            # print(f"{tmp}, {type(tmp)}")
            tmp = ord(data[i]) ^ 0x69

            packet_start = 0x69

            # case waiting_for_start:
            if(s == 0):
                if(tmp == packet_start):
                    self.start = tmp
                    self.payload = []
                    self.deserializer_state = 1
                    
            
            # case waiting_for_type:
            elif(s == 1):
                self.message_type = tmp
                self.deserializer_state = 2
                

            # case waiting_for_len:
            elif(s == 2):
                self.message_lenght = tmp
                self.deserializer_state = 3
                
            
            # case waiting_for_crc:
            elif(s == 3):
                self.crc = tmp
                self.deserializer_state = 4
                
            # case data_acquisition:
            elif(s == 4):
                self.payload.append(tmp)

            # print(f'{len(self.payload)}, {self.message_lenght}, {self.deserializer_state }, {tmp}')
            if(len(self.payload) == self.message_lenght and self.deserializer_state == 4):
                try:
                    tmp_crc = (sum([ord(c) for c in str(bytes(self.payload), 'utf-8')]) + len(self.payload)) % 256
                    if(tmp_crc == self.crc):
                        self.callback(self.message_type, self.payload)
                except:
                    print("Unhandled packet")           
                
                if(i > 0): 
                    i -= 1
                self.deserializer_state = 0

class communication:
    devices = dict()
    radio_alive = False

    def get_ports(this):
        res = []
        ports = list_ports.comports()

        for port, desc, hwid in sorted(ports):
            res.append("{}".format(desc))
            this.devices[desc] = port

        return res

    def get_radio_connection(this, name):
        try:
            this.radio = serial.Serial(this.devices[name], 38400)
            this.radio_alive = True
            return True
        except:
            return False

        
    
    def send_data_over_radio(this, data, type):
        try:
            packet = Packet(type, data).get_packet()
            this.radio.write(code_decode(packet))
        except:
            pass

    def read_data_over_radio(this):
        try:
            if(this.radio.inWaiting() > 0):
                return this.radio.read(1)
            else:
                return None
            # this.radio.write(code_decode(packet))
        except:
            return None

    def close_radio_connection(this):
        try:
            this.radio.close()
        except:
            pass

def time_ms():
    return int(time.time() * 1000)
    
states = {
    'diag' : [],
    'GPS'  : [],
    'IMU'  : []
}

coords = {
        'longitude' : 0,
        'latitude' : 0
    }

communicates_radio = queue.Queue(512)
communicates_unirover = queue.Queue(512)

requests_radio = queue.Queue(512)
requests_unirover = queue.Queue(512)


def stringify(list_of_ints):
    return ''.join([chr(c) for c in list_of_ints])

def uni_callback(type, payload):
    global communicates_unirover
    global requests_unirover
    global states

    if(type == 0):
        communicates_unirover.put_nowait({'type' : 0, 'payload' : ''})
    
    elif(type == 7 or type == 2):
        states['diag'] = payload
        requests_unirover.put_nowait({'unirover_request' : ['sensor_data'], 'data' : states})

    elif(type == 4):
        states['GPS'] = payload
        requests_unirover.put_nowait({'unirover_request' : ['sensor_data'], 'data' : states})
    
    elif(type == 3):
        states['IMU'] = payload
        requests_unirover.put_nowait({'unirover_request' : ['sensor_data'], 'data' : states})
        
    # print(states)

def radio_callback(type, payload):
    global communicates_radio
    global requests_radio
    global coords
    
    if(type == 0):
        communicates_radio.put_nowait({'type' : 0, 'payload' : ''})

    elif (type == 100):
        coords = stringify(payload)
        requests_radio.put_nowait({
            'radio_request' : ['coords', 'set_mode'], 
            'coords' : coords, 
            'mode' : 'auto'
        })

    elif(type == 101):
        # print(stringify(payload))
        drive = stringify(payload)
        requests_radio.put_nowait({
            'radio_request' : ['drive', 'set_mode'], 
            'drive' : drive, 
            'mode' : 'man'
        })

def radio_process(pipe):
    global communicates_radio
    global requests_radio
    global coords

    radio = communication()
    radio_deserializer = dePacket(radio_callback)

    while True:
        tmp = radio.get_ports()
        if('USB2.0-Ser!' in tmp):
            radio.get_radio_connection('USB2.0-Ser!')
        
        if(radio.radio_alive):
            break

    print('Radio connected')
    while True:
        read_radio = []
        tmp = radio.read_data_over_radio()
        
        if(tmp != None):
            read_radio.append(tmp)
        
        radio_deserializer.deserialize(read_radio)

        if(pipe.poll(0.005)):
            tmp = pipe.recv()

            if('send_packet' in tmp['main_request']):
                radio.send_data_over_radio(tmp['payload'], tmp['type'])

        while(not requests_radio.empty()):
            pipe.send(requests_radio.get_nowait())

    # radio.close_radio_connection()


def unirover_process(pipe):
    global communicates_unirover
    global requests_unirover
    global states

    unirover = communication()
    uni_deserializer = dePacket(uni_callback, True)

    while True:
        tmp = unirover.get_ports()
        if('UNIRover' in tmp):
            unirover.get_radio_connection('UNIRover')
        
        if(unirover.radio_alive):
            break

    print('UNIRover connected')
    while True:
        read_unirover = []
        tmp = unirover.read_data_over_radio()
        
        if(tmp != None):
            read_unirover.append(tmp)
        
        uni_deserializer.deserialize(read_unirover)

        if(pipe.poll(0.005)):
            tmp = pipe.recv()

            if('get_sensors' in tmp['main_request']):
                unirover.send_data_over_radio('', 8)
                unirover.send_data_over_radio('', 7)
            if('set_mode' in tmp['main_request']):
                unirover.send_data_over_radio(tmp['mode'], 5)
            if('set_drive' in tmp['main_request']):
                pwm_left = tmp['left']
                pwm_right = tmp['right']
                dir_left = 'R'
                dir_right = 'R'

                if(pwm_left >= 0):
                    dir_left = 'F'
                if(pwm_right >= 0):
                    dir_right = 'F'

                unirover.send_data_over_radio(f'L{dir_left}{pwm_left}', 1)
                unirover.send_data_over_radio(f'R{dir_right}{pwm_right}', 1)
            if('set_cam' in tmp['main_request']):
                flags = tmp['cam']
                if(flags & 8):
                    unirover.send_data_over_radio('DF', 1) # RIGHT
                if(flags & 4):
                    unirover.send_data_over_radio('DR', 1) # LEFT
                if(flags & 2):
                    unirover.send_data_over_radio('S+', 1) # UP
                if(flags & 1):
                    unirover.send_data_over_radio('S-', 1) # DOWN
        
        while(not requests_unirover.empty()):
            pipe.send(requests_unirover.get_nowait())
    # unirover.close_radio_connection()
    

    
sensor_data = {
        'diag' : [],
        'GPS'  : [],
        'IMU'  : []
    }

actual_coords = []
desired_coords = []

mode = 'man'

def translate_drive(data):
    ctrl = {
        'left' : 0,
        'right': 0,
        'cam'  : 0
    }

    tmp = data.split(',')
    if(len(tmp == 1)):
        ctrl['cam'] = int(tmp[0][1])
    elif(len(tmp == 2)):
        ctrl['left'] = int(tmp[0][1:]) * 1000 - 1
        ctrl['right'] = int(tmp[1]) * 1000 - 1

    return ctrl

def run_comm():
    global sensor_data
    global actual_coords
    global desired_coords
    global mode

    pipe_to_radio, radio_to_comm = multiprocessing.Pipe()  
    pipe_to_unirover, unirover_to_comm = multiprocessing.Pipe()  

    radio_proc = multiprocessing.Process(target=radio_process, name="radio_process", args=tuple(radio_to_comm))
    unirover_proc = multiprocessing.Process(target=unirover_process, name="UNIRover_process", args=tuple(unirover_to_comm))

    radio_proc.start()
    unirover_proc.start()

    data_timer = time_ms()
    sensor_timer = time_ms()

    i = 0

    while True:
        if(time_ms() - data_timer > 500):
            if(i == 0):
                pipe_to_radio.send({
                    'main_request' : ['send_packet'],
                    'type' : 7,
                    'payload' : stringify(sensor_data['diag'])
                })
                i = 1
            elif(i == 1):
                pipe_to_radio.send({
                    'main_request' : ['send_packet'],
                    'type' : 3,
                    'payload' : stringify(sensor_data['IMU'])
                })
                i = 2
            elif(i == 2):
                pipe_to_radio.send({
                    'main_request' : ['send_packet'],
                    'type' : 4,
                    'payload' : stringify(sensor_data['GPS'])
                })
                i = 0
            data_timer = time_ms()

        if(time_ms() - sensor_timer > 100):
            pipe_to_unirover.send({
                'main_request' : ['get_sensors', 'set_mode'],
                'mode' : 'M' if mode == 'man' else 'A'
            })
            sensor_timer = time_ms()
        

        if(pipe_to_radio.poll(0.005)):
            tmp = pipe_to_radio.recv()
            
            if('drive' in tmp['radio_request']):
                drive = translate_drive(tmp['drive'])
                pipe_to_unirover.send({
                    'main_request' : ['set_drive', 'set_cam'],
                    'left' : drive['left'],
                    'right': drive['right'],
                    'cam'  : drive['cam']
                })
            if('coords' in tmp['radio_request']):
                desired_coords = tmp['coords']
            if('set_mode' in tmp['radio_request']):
                mode = tmp['mode']
            
        if(pipe_to_unirover.poll(0.005)):
            tmp = pipe_to_unirover.recv()

            if('sensor_data' in tmp['unirover_request']):
                sensor_data = tmp['data']
run_comm()