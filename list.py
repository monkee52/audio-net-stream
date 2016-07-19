import pyaudio

audio = pyaudio.PyAudio()

try:
    device_length = audio.get_device_count()

    for i in range(device_length):
        info = audio.get_device_info_by_index(i)

        host_api_info = audio.get_host_api_info_by_index(info["hostApi"])
        name = host_api_info["name"] + "|" + info["name"]

        if name[:8] == "Windows ":
            name = name[8:]

        print(name)
        print(" - Inputs: %d" % info["maxInputChannels"])
        print(" - Outputs: %d" % info["maxOutputChannels"])
finally:
    audio.terminate()
