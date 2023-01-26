from controller import Controller

# import midi
# import sf2_loader as sf
# import os
# from programs import PROGRAMS
#
# def convert_to_wav(load_path):
#     soundfont = "/Users/agear/Documents/Projects/AGM/soundfont/gm.sf2"
#     loader = sf.sf2_loader(soundfont)
#
#     filename_w_ext = os.path.basename(load_path)
#     songname, file_extension = os.path.splitext(filename_w_ext)
#     save_dir=f'./{songname}_midi_stems'
#     os.mkdir(save_dir)
#
#
#     for filename in os.listdir(load_path):
#         f = os.path.join(load_path, filename)
#         # checking if it is a file
#         if os.path.isfile(f) and f[-4:] == ".mid":
#             print(filename)
#
#             loader.export_midi_file(fr'{f}', name=f'./audio_stems/{filename}.wav', format='wav')
#
#
# def extract_midi_stems(file_path):
#
#
#     filename_w_ext = os.path.basename(file_path)
#     songname, file_extension = os.path.splitext(filename_w_ext)
#     save_dir=f'./{songname}_midi_stems'
#     os.mkdir(save_dir)
#
#     midi_multitrack = midi.read_midifile(file_path)
#     for i, track in enumerate(midi_multitrack):
#         for event in track:
#             print(event)
#             if type(event) == midi.ProgramChangeEvent:
#                 if event.channel == 9:
#                     track_name = "0 - Drum Kit 0"
#                 # print(PROGRAMS[event.data[0]+1])
#                 else:
#                     track_name = PROGRAMS[event.data[0]+1]
#                 break
#
#         pattern = midi.Pattern()
#         pattern.append(track)
#         midi.write_midifile(f"{save_dir}/{songname} - 0{i+1} - {track_name}.mid", pattern)
#         # print('\n\n\n\n\n\n\n*******\n\n\n\n\n\n')
#
#
# def main():
#     print('hello world')
#
#     file_path="/Users/agear/Documents/Projects/AGM/Guitar Pro PDFs/Finished/Aphids/Aphids2.mid"
#
#     filename_w_ext = os.path.basename(file_path)
#     print(filename_w_ext)
#     filename, file_extension = os.path.splitext(filename_w_ext)
#     print(filename)
#     print(file_extension)
#     path, filename = os.path.split(file_path)
#     print(path)
#     print(filename)
#
#     extract_midi_stems(file_path=file_path)
#     convert_to_wav(load_path=f"./{filename}_midi_stems")
#
#     # give midi file to work on
#     # create folder to save .mid files in
#     # extract and save each .mid stem
#     # import
#
# main()

def main():
    # TODO Add git ignore
    # TODO Figure out why drum tracks aren't named
    # TODO remove print statements
    # TODO Encapsulate track???
    # TODO first track should be 01
    # TODO Figure out reverb
    # TODO Add time calculator
    # TODO Add multithreading

    # midi_file_path="/Users/agear/Documents/Projects/AGM/Guitar Pro PDFs/Finished/Aphids/Aphids2.mid"
    # midi_file_path="/Users/agear/Documents/Projects/AGM/Guitar Pro PDFs/Finished/0.7/0.71.mid"
    # midi_file_path="/Users/agear/Documents/Projects/AGM/Guitar Pro PDFs/Finished/Aleksei's Visions of Chess War/Aleksei's Visions of Chess War.mid"
    midi_file_path="/Users/agear/Documents/Projects/AGM/Guitar Pro PDFs/Finished/The Human Body (Can Run On Sugar Alone Goddamnit!)/The human body can run on sugar alone, God damn it!8.mid"


    controller = Controller(midi_file_path)
    controller.extract_midi_stems()
    controller.convert_to_wav(path=controller.midi_stem_path)

main()
