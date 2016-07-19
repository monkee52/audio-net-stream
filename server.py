import pyaudio
import time
import socket
import struct

DESTINATION = ("239.255.64.87", 8132)

SAMPLE_RATE = 96000
CHANNELS = 2
FORMAT = pyaudio.paInt16
BUFFER_SIZE = 64

DEVICE = "WDM-KS|Mic 1 (Virtual Cable 1)"

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)

s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

addr = struct.unpack(">L", socket.inet_aton(DESTINATION[0]))[0]

if addr == 4294967295: # Broadcast
    s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
elif addr >= 3758096384 and addr <= 4026531839: # Multicast
    s.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 1)

bit_rate = SAMPLE_RATE * CHANNELS * pyaudio.get_sample_size(FORMAT) * 8

print("Rate:   %d b/s" % bit_rate)
print("Sample: %f us" % (1000000 / SAMPLE_RATE))
print("Delay:  %f us" % (1000000 / SAMPLE_RATE * BUFFER_SIZE))

header = struct.pack(">5sHLBhh", b"AUDIO", 0x0100, SAMPLE_RATE, CHANNELS, FORMAT, BUFFER_SIZE)

t = time.time()
sent_total = 0
seq_number = int(time.time())

def callback(in_data, frame_count, time_info, status_flags):
    global sent_total, seq_number
    
    sent_total += s.sendto(header + struct.pack(">Q", seq_number) + in_data, DESTINATION)
    seq_number += 1
    
    return (None, 0)

audio = pyaudio.PyAudio()

try:
    device_length = audio.get_device_count()
    index = -1

    for i in range(device_length):
        info = audio.get_device_info_by_index(i)

        if info["maxInputChannels"] > 0:
            host_api_info = audio.get_host_api_info_by_index(info["hostApi"])
            name = host_api_info["name"] + "|" + info["name"]

            if name[:8] == "Windows ":
                name = name[8:]

            if name == DEVICE:
                index = i
                break

    if index == -1:
        print("Device not found - defaulting")
        index = audio.get_default_input_device_info()["index"]

    stream = audio.open(SAMPLE_RATE, CHANNELS, FORMAT, True, False, index, None, BUFFER_SIZE, True, None, None, callback)

    stream.start_stream()

    try:
        while stream.is_active():
            t_now = time.time()

            if t_now - t > 1 / 15:
                print("\rSent %d B" % sent_total, end = "")
                t = t_now
            
            time.sleep(0.1)
    except KeyboardInterrupt:
        pass

    stream.stop_stream()
    stream.close()
finally:
    s.close()
    audio.terminate()
