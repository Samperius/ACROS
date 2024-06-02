import os

dirname = os.path.dirname(__file__)
print(dirname)


INITIAL_FILENAME = os.getenv("INITIAL_FILENAME") or "experiment_saved_3_completed_4_generated.csv"
INITIAL_FILE_PATH = os.path.join(dirname,  INITIAL_FILENAME)
SAVE_FILENAME = os.getenv("SAVE_FILENAME") or "experiment_saved.csv"
SAVE_FILE_PATH = os.path.join(dirname,  SAVE_FILENAME)
RESULT_FILENAME = os.getenv("RESULT_FILENAME") or "SogCou_4_x.csv"
RESULT_FILE_PATH = os.path.join(dirname,  ".", "data", RESULT_FILENAME)
EXPERIMENT_NAME = 'sonogoshira-coupling'