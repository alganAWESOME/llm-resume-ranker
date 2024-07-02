import anthropic
import base64
from random import randint
import os

class LLMResumeComparer:
    PROMPT = """"You are an expert technical recruiter at a big tech company looking to hire graduate software engineers. Your task is to evaluate the following two early-career software engineer resumes. Only after discussing your reasoning, state which resume you prefer. You may refer to the resumes as Resume A and Resume B respectively.

Criteria for evaluation:
- Technical depth: how much technical depth and experience does the candidate demonstrate? You should mostly discard non-software engineering experience, e.g. retail or marketing.
- Clarity of communication: is it easy to understand what exactly the candidate worked on, and what the impact was? Is the candidate using buzzwords that sound out of place?
- Appearance: the resume should look professional and simple, minimising flashy graphics as much as possible. Is there attention to detail, e.g. good whitespace and flawless spelling?
- University: universities should be ranked as follows: Oxford/Cambridge, Imperial, Warwick/UCL, other Russell Group, non-Russell Group. Note that some resumes may anonymise their university.
- Miscellaneous: any other observation as you see fit."""

    def __init__(self):
        self.client = anthropic.Anthropic()

    @staticmethod
    def get_image_data(ranked: bool, image_filename):
        path = f'./{'ranked' if ranked else 'unranked'}/{image_filename}' # e.g. ./unranked/CV.png

        with open(path, 'rb') as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
        
    def construct_resumes_dict(self, unranked_filename, ranked_filename):
        ranked_data = self.get_image_data(ranked=True, image_filename=ranked_filename)
        unranked_data = self.get_image_data(ranked=False, image_filename=unranked_filename)

        # Are the images jpg or png
        get_image_type = lambda image_filename: 'jpeg' if image_filename.split('.')[1] == 'jpg' else 'png'
        ranked_type, unranked_type = get_image_type(ranked_filename), get_image_type(unranked_filename)

        # Randomise which one will be called Resume A and Resume B
        resumes = {'Resume A': {}, 'Resume B': {}}
        my_randint = randint(0, 1)
        if my_randint == 0:
            self.to_be_ranked_is_A = False
            resumes['Resume A']['filename'] = ranked_filename
            resumes['Resume A']['data'] = ranked_data
            resumes['Resume A']['type'] = ranked_type
            resumes['Resume B']['filename'] = unranked_filename
            resumes['Resume B']['data'] = unranked_data
            resumes['Resume B']['type'] = unranked_type
        else:
            self.to_be_ranked_is_A = True
            resumes['Resume B']['filename'] = ranked_filename
            resumes['Resume B']['data'] = ranked_data
            resumes['Resume B']['type'] = ranked_type
            resumes['Resume A']['filename'] = unranked_filename
            resumes['Resume A']['data'] = unranked_data
            resumes['Resume A']['type'] = unranked_type

        self.current_resumes = resumes

    def compare_resumes_with_llm(self):
        mediatype_A = f"image/{self.current_resumes['Resume A']['type']}"
        mediatype_B = f"image/{self.current_resumes['Resume B']['type']}"

        print("Comparing resumes...")

        message = self.client.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=1000,
        temperature=0,
        messages=[
            {

                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Resume A:"
                    },
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": mediatype_A,
                            "data": self.current_resumes['Resume A']['data']
                        }
                    },
                    {
                        "type": "text",
                        "text": "Resume B:"
                    },
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": mediatype_B,
                            "data": self.current_resumes['Resume B']['data']
                        }
                    },
                    {
                        "type": "text",
                        "text": self.PROMPT
                    }
                ]
            }
        ]
    )
        
        if 'prefer resume a' in message.content[0].text.lower():
            winner = 'Resume A'
        elif 'prefer resume b' in message.content[0].text.lower():
            winner = 'Resume B'
        else:
            winner = None
            print("WARNING: Claude did not state winner")
        
        return {'Resume A': self.current_resumes['Resume A']['filename'],
                 'Resume B': self.current_resumes['Resume B']['filename'],
                 'winner': winner, # "Resume A" or "Resume B"
                 'to_be_ranked_resume': 'Resume A' if self.to_be_ranked_is_A else 'Resume B',
                 'claude_response': message.content[0].text}

    def main(self, unranked_filename, ranked_filename):
        self.construct_resumes_dict(unranked_filename, ranked_filename)
        return self.compare_resumes_with_llm()
    
if __name__ == "__main__":
    resume_comparer = LLMResumeComparer()
    comparison = resume_comparer.main('CV_V1_11-1.png', '002-CV.jpg')
    print(comparison)