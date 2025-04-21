import streamlit as st

import os

from typing import List
from pydantic import BaseModel, Field

from langchain_google_genai import ChatGoogleGenerativeAI

import json
import random
import boto3

from cryptography.fernet import Fernet as F
from typing import Union

st.set_page_config(layout = "wide")

os.environ["GOOGLE_API_KEY"] = st.secrets["GOOGLE_API_KEY"]

class AlternateOptions(BaseModel):
    "Alternate Confusing Options Depending on the Difficulty Selected."
    false_option_1 : str = Field(description = "Alternate Confusing option 1 Depending on the Difficulty Selected.")
    false_option_2 : str = Field(description = "Alternate Confusing option 2 Depending on the Difficulty Selected.")
    false_option_3 : str = Field(description = "Alternate Confusing option 3 Depending on the Difficulty Selected.")

st.title("Vocabulary Memorization Tool")

st.divider()

@st.cache_data(show_spinner = False)
def get_options(word : str, meaning : str, difficulty : int) -> AlternateOptions:
    llm = ChatGoogleGenerativeAI(model = "gemini-2.0-flash-lite")
    structured_llm = llm.with_structured_output(AlternateOptions)
    return structured_llm.invoke(f"{word}. Meaning - {meaning}. Create 3 similar confusing meanings, Difficulty level - {difficulty}. I will show the user the word and have the user choose the meaning, so I 3 similar confusing meanings according to the chosen difficulty (either 'Easy', 'Moderate', 'Difficult' or 'HARDEST ☠️') where HARDEST should be insanely difficult. ONLY GIVE MEANINGS.")

if "progress" not in st.session_state:
    st.session_state.progress = "selection"

def end_test():
    st.session_state.progress = "final_result"

def decrypt_message(key : str, msg : Union[str, bytes]) -> str:
    encoded_key = key if isinstance(key, bytes) else key.encode()
    handler = F(encoded_key)
    encoded_msg = msg if isinstance(msg, bytes) else msg.encode()
    treatment = handler.decrypt(encoded_msg)
    return str(treatment, 'utf-8')

def fetch_data_s3() -> str:
    s3 = boto3.client('s3', region_name = 'ap-south-1', aws_access_key_id = st.secrets["ACCESS_KEY"], aws_secret_access_key = st.secrets["SECRET_KEY"])
    response = s3.get_object(Bucket = st.secrets["BUCKET_NAME"], Key = st.secrets["PREFIX"])
    return response['Body'].read().decode('utf-8')

@st.cache_data
def load_questions():
    encrypted_string = fetch_data_s3()
    decrypted_string = decrypt_message(st.secrets["KEY"], encrypted_string)
    return json.loads(decrypted_string)

questions = load_questions()

def start_test(difficulty : str, num_questions : int):
    st.session_state.difficulty = difficulty
    st.session_state.num_questions = num_questions
    sampled_keys = random.sample(list(questions.keys()), num_questions)
    sampled_items = {key : questions[key] for key in sampled_keys}
    st.session_state.questions = sampled_items
    st.session_state.progress_index = 0
    st.session_state.progress = "test"
    st.session_state.correct = []
    st.session_state.wrong = []

if st.session_state.progress == "selection":
    difficulty = st.select_slider(label = "Select Difficulty -", options = ["Easy", "Moderate", "Difficult", "HARDEST ☠️"])
    num_questions = st.number_input(label = "Number of Questions -", min_value = 3, max_value = 100)
    st.button(label = "Start", on_click = start_test, kwargs = {"difficulty" : difficulty, "num_questions" : num_questions})

def next_question(option_selected : str, correct_option : str, word : str):
    if option_selected == correct_option:
        st.session_state.correct.append(word)
    else:
        st.session_state.wrong.append(word)
    if st.session_state.progress_index == st.session_state.num_questions - 1:
        st.session_state.progress = "result"
    else:
        st.session_state.progress_index += 1
    return

def decrypt_message(key: str, msg: Union[str, bytes]) -> str:
    encoded_key = key if isinstance(key, bytes) else key.encode()
    handler = F(encoded_key)
    encoded_msg = msg if isinstance(msg, bytes) else msg.encode()
    treatment = handler.decrypt(encoded_msg)
    return str(treatment, 'utf-8')

if st.session_state.progress == "test":
    questions_subset_list = list(st.session_state.questions.keys())
    name = questions_subset_list[st.session_state.progress_index]
    st.subheader(name)
    correct = st.session_state.questions[name]["Definition"].replace("T o ", "To ")
    options = get_options(name, correct, st.session_state.difficulty)
    options_appended = [correct, options.false_option_1, options.false_option_2, options.false_option_3]
    random.shuffle(options_appended)
    st.button(label = options_appended[0], on_click = next_question, kwargs = {"option_selected" : options_appended[0], "correct_option" : correct, "word" : name})
    st.button(label = options_appended[1], on_click = next_question, kwargs = {"option_selected" : options_appended[0], "correct_option" : correct, "word" : name})
    st.button(label = options_appended[2], on_click = next_question, kwargs = {"option_selected" : options_appended[0], "correct_option" : correct, "word" : name})
    st.button(label = options_appended[3], on_click = next_question, kwargs = {"option_selected" : options_appended[0], "correct_option" : correct, "word" : name})

def reset():
    st.session_state.progress = "selection"

if st.session_state.progress == "result":
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Correct")
        st.write(st.session_state.correct)
    with col2:
        st.subheader("Wrong")
        st.write(st.session_state.wrong)
    st.button("Main Page", on_click = reset)