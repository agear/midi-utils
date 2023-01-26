from controller import Controller

def main():
    # TODO Add git ignore
    # TODO Figure out why drum tracks aren't named
    # TODO remove print statements
    # TODO Encapsulate track???
    # TODO first track should be 01
    # TODO Figure out reverb
    # TODO Add time calculator
    # TODO Add multithreading
    # TODO Don't bounce empty tracks (drums)
    # TODO add test suite
    # TODO add type hints

    # midi_file_path="/Users/agear/Documents/Projects/AGM/Guitar Pro PDFs/Finished/Aphids/Aphids2.mid"
    # midi_file_path="/Users/agear/Documents/Projects/AGM/Guitar Pro PDFs/Finished/0.7/0.71.mid"
    # midi_file_path="/Users/agear/Documents/Projects/AGM/Guitar Pro PDFs/Finished/Aleksei's Visions of Chess War/Aleksei's Visions of Chess War.mid"
    midi_file_path="/Users/agear/Documents/Projects/AGM/Guitar Pro PDFs/Finished/The Human Body (Can Run On Sugar Alone Goddamnit!)/The human body can run on sugar alone, God damn it!8.mid"


    controller = Controller(midi_file_path)
    controller.extract_midi_stems()
    controller.convert_to_wav(path=controller.midi_stem_path)

main()
