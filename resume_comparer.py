import anthropic
import base64
from random import randint

class LLMResumeComparer:
    PROMPT = """You are an expert software engineering recruiter tasked with comparing two resumes for an early-career software engineering position. Your goal is to analyze both resumes thoroughly and determine which candidate would be a better fit for the role.

Please follow these steps:

1. Carefully review both resumes, paying attention to education, work experience, projects, technical skills, and any other relevant information.

2. For each resume, list the key strengths and potential weaknesses or areas of concern.

3. Compare the resumes based on the following criteria, sorted from most relevant to least relevant:
   - Relevance and and amount of work experience
   - Depth and breadth of technical skills
   - Education and academic performance
   - Project experience and its relevance to software engineering
   - Evidence of problem-solving abilities and initiative

4. Furthermore, the following are negative criteria, which should be discarded or treated as less relevant factors:
   - IGNORE Work experience that is not directly relevant to software engineering, such as retail jobs.
   - IGNORE Certifications, such as those from Coursera or other MOOCs.
   - IGNORE Leadership roles and extracurricular activities.
   - IGNORE Grades from before university (highschool grades).
   - IGNORE How far into the degree the candidate is; it doesn't matter if they are a graduate, near graduation or still a few years away from graduation.

5. Consider how well each candidate's background aligns with typical requirements for an early-career software engineering role.

6. Weigh the pros and cons of each resume, considering which candidate is likely to perform better in the role and have more potential for growth.

7. After thorough analysis and comparison, form your conclusion about which resume you prefer.

8. Explain your reasoning in detail, covering all the points you considered in your decision-making process.

9. Only after providing your complete analysis and reasoning, state your final decision by writing either "I prefer Resume A" or "I prefer Resume B" as the very last line of your response.

Remember, your goal is to provide a comprehensive comparison and justification for your choice before stating your final preference."""

    HAIKU = "claude-3-haiku-20240307"
    SONNET = "claude-3-5-sonnet-20240620"

    def __init__(self, resume_folder, model='sonnet', temperature=0):
        self.resume_folder = resume_folder
        self.model = model
        self.temperature = temperature
        self.client = anthropic.Anthropic()

        self.num_calls = {'haiku': 0, 'sonnet': 0}

        self.should_swap_mediatype = False

    def get_image_data(self, image_filename):
        path = f'{self.resume_folder}/ranked/{image_filename}'

        with open(path, 'rb') as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
        
    def construct_resumes_dict(self, resume1, resume2):
        data1 = self.get_image_data(image_filename=resume1)
        data2 = self.get_image_data(image_filename=resume2)

        # Are the images jpg or png
        get_image_type = lambda image_filename: 'jpeg' if image_filename.split('.')[1] == 'jpg' else 'png'
        image_type1, image_type2 = get_image_type(resume1), get_image_type(resume2)

        # Construct dictionary containing the two resumes
        resumes_dict = {'Resume A': {}, 'Resume B': {}}
        self.A_is_1 = True
        resumes_dict['Resume A']['filename'] = resume1
        resumes_dict['Resume A']['data'] = data1
        resumes_dict['Resume A']['type'] = image_type1
        resumes_dict['Resume B']['filename'] = resume2
        resumes_dict['Resume B']['data'] = data2
        resumes_dict['Resume B']['type'] = image_type2

        return resumes_dict

    def randomise_resumes(self, resumes_dict):
        rand_int = randint(0, 1)
        # if rand_int is 1 swap resume A and B  
        if rand_int:
            temp = resumes_dict['Resume A']
            resumes_dict['Resume A'] = resumes_dict['Resume B']
            resumes_dict['Resume B'] = temp
            self.A_is_1 = not self.A_is_1

    def compare_resumes_with_llm(self, resumes_dict):
        
        self.randomise_resumes(resumes_dict)

        mediatype_A = f"image/{resumes_dict['Resume A']['type']}"
        mediatype_B = f"image/{resumes_dict['Resume B']['type']}"

        def call_claude():
            return self.client.messages.create(
            model = self.SONNET if self.model == 'sonnet' else self.HAIKU,
            max_tokens=2000,
            temperature=self.temperature,
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
                                "data": resumes_dict['Resume A']['data']
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
                                "data": resumes_dict['Resume B']['data']
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

        # try:
        #     self.should_swap_mediatype = False
        #     message = call_claude()
        # except:
        #     # Error is most likely because mediatype was wrong
        #     if self.A_is_1:
        #         # Switch jpeg to png or vice versa
        #         mediatype_A = 'image/jpeg' if mediatype_A == 'image/png' else 'image/png'
        #     else:
        #         mediatype_B = 'image/jpeg' if mediatype_B == 'image/png' else 'image/png'

        #     # Signal that rename is required
        #     self.should_swap_mediatype = True

        #     # Retry
        #     message = call_claude()

        message = call_claude()
        
        if 'prefer resume a' in message.content[0].text.lower():
            winner = 'Resume A'
        elif 'prefer resume b' in message.content[0].text.lower():
            winner = 'Resume B'
        else:
            winner = None
            print("WARNING: Claude did not state winner")
            print('here is what it said:')
            print(message.content[0].text)
            input('Press Any Key To Continue')
        
        return {'Resume A': resumes_dict['Resume A']['filename'],
                 'Resume B': resumes_dict['Resume B']['filename'],
                 'winner': winner, # "Resume A" or "Resume B"
                 'resume1': 'Resume A' if self.A_is_1 else 'Resume B',
                 'claude_response': message.content[0].text}

    @staticmethod
    def pretty_print(comparison):
        """Pretty prints comparison dictionary."""
        for key, value in comparison.items():
            if key == 'claude_response':
                print(f'Claude:\n{value}')
            else:
                print(f'{key}: {value}')

    def compare_resumes(self, resume1, resume2):
        print(f"Comparing {resume1} vs {resume2}...")
        resumes_dict = self.construct_resumes_dict(resume1, resume2)
        return self.compare_resumes_with_llm(resumes_dict)
    
if __name__ == "__main__":
    resume_comparer = LLMResumeComparer(resume_folder='resumes_uk', model='haiku', temperature=0)
    comparison = resume_comparer.compare_resumes('1376-remers.png', '1311-bark.png')
    resume_comparer.pretty_print(comparison)

"""
BACKLOG

- write a function that pretty-prints a `comparison` dictionary (ideally make a `Comparison` object)
- modify best of n comparison so that it accepts an initial value for wins / losses
- create timers + api cost calculators
"""