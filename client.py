import pyaudio
import time
import socket
import struct

ADDRESS = ("239.255.64.87", 8132)

DEVICE = "MME|Speakers (Conexant 20671 SmartA"

CHUNK = 32 * 1024

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)

s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

if len(ADDRESS[0]) > 0:
    addr = struct.unpack(">L", socket.inet_aton(ADDRESS[0]))[0]

    if addr >= 3758096384 and addr <= 4026531839: # Multicast
        s.bind(("", ADDRESS[1]))
        s.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, struct.pack("4sl", socket.inet_aton(ADDRESS[0]), socket.INADDR_ANY))
    else:
        s.bind((ADDRESS[0], ADDRESS[1]))
else:
    s.bind(("", ADDRESS[1]))

audio = pyaudio.PyAudio()

try:
    device_length = audio.get_device_count()
    index = -1

    for i in range(device_length):
        info = audio.get_device_info_by_index(i)

        if info["maxOutputChannels"] > 0:
            host_api_info = audio.get_host_api_info_by_index(info["hostApi"])
            name = host_api_info["name"] + "|" + info["name"]

            if name[:8] == "Windows ":
                name = name[8:]

            if name == DEVICE:
                index = i
                break

    if index == -1:
        print("Device not found - defaulting")
        index = audio.get_default_output_device_info()["index"]

    stream = None
    
    stream_sample_rate = -1
    stream_channels = -1
    stream_format = -1
    stream_buffer = -1
    
    seq_number = int(time.time())
    running = True

    try:
        while running:
            data = s.recv(CHUNK)

            if len(data) < 24:
                continue

            if data[:5] != b"AUDIO":
                continue

            header = struct.unpack(">5sHLBhhQ", data[:24])

            if header[1] != 0x0100:
                continue

            if header[2] != stream_sample_rate or header[3] != stream_channels or header[4] != stream_format or header[5] != stream_buffer or stream == None:
                stream_sample_rate = header[2]
                stream_channels = header[3]
                stream_format = header[4]
                stream_buffer = header[5]
                seq_number = header[6] - 1
                
                if stream != None:
                    stream.stop_stream()
                    stream.close()

                print("Starting stream")

                stream = audio.open(stream_sample_rate, stream_channels, stream_format, False, True, None, index, stream_buffer, True, None, None, None)

            if header[6] > seq_number:
                if header[6] - seq_number > 1:
                    print("\rDropped %d frame(s)" % (header[6] - seq_number))
                
                seq_number = header[6]

                stream.write(data[24:])
    except KeyboardInterrupt:
        pass

    if stream != None:
        stream.stop_stream()
        stream.close()
finally:
    s.close()
    audio.terminate()
