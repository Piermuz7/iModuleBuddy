import pandas as pd
from langchain_anthropic import ChatAnthropic
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

# Load the data
modules_df = pd.read_csv('.\\csv\\modules_truncated.csv')
skills_df = pd.read_csv('.\\csv\\skills.csv')
knowledge_df = pd.read_csv('.\\csv\\knowledge.csv')

# Configure Langchain Community with Anthropic Claude
llm = ChatAnthropic(temperature=0,
                    anthropic_api_key="",
                    model_name="claude-3-5-sonnet-20240620")


# Sample function for querying Claude 3.5 using Langchain Community
def get_learning_outcomes(modules_df, skills_df, knowledge_df):
    # Constructing the skills and knowledge lists
    skills_list = "\n".join([f"{row['index']} {row['skill']}" for _, row in skills_df.iterrows()])
    knowledge_list = "\n".join([f"{row['index']} {row['knowledge']}" for _, row in knowledge_df.iterrows()])

    # Initializing the output
    output = 'Module Title, Learning Outcomes, Promoted Skills and Knowledge, Explanation\n'

    # Define the prompt template
    prompt_template = """
    Hello,
    I have module descriptions and lists of skill and knowledge concepts. Now I need a table with the learning outcomes that students can expect to gain from the module solely based on the module descriptions and map them to the skill and knowledge concepts they promote.
    To begin, I will provide you with two lists: one containing concepts of skills, and another containing concepts of knowledge. These lists will serve as the reference for your analysis.
    Here are the lists of skills and knowledge:
    Skills:
    {skills_list}

    Knowledge:
    {knowledge_list}

    {module_description_prompt}

    Make your analysis in a csv file with the following columns:
    • Module Title
    • Learning Outcomes
    • Promoted Skills and Knowledge
    • Explanation

    The answer must be the csv file, without any additional information.
    """

    prompt = PromptTemplate(
        input_variables=["skills_list", "knowledge_list", "module_description_prompt"],
        template=prompt_template
    )

    llm_chain = LLMChain(llm=llm, prompt=prompt)

    # Loop through each module description
    for _, module_row in modules_df.iterrows():
        module_title = module_row['Individual Name']
        module_text = module_row['Course_Description']
        module_comment = module_row['Course_Comment']
        module_objectives = module_row['Course_Competency_to_be_achieved']
        module_content = module_row['Course_Content']

        # Creating the module description prompt
        module_description_prompt = f"""
        This is the module description:
        Module Title: {module_title}
        Module Text: {module_text}
        Module Comment: {module_comment}
        Module Objectives: {module_objectives}
        Module Content: {module_content}
        """

        # Running the LLM chain to generate the response
        response = llm_chain.invoke({
            "skills_list": skills_list,
            "knowledge_list": knowledge_list,
            "module_description_prompt": module_description_prompt,
        })
        response = response['text'].splitlines()
        output += '\n'.join(response[1:])
    with open('learning_outcomes.csv', 'w') as file:
        file.write(output)


# call the function
get_learning_outcomes(modules_df, skills_df, knowledge_df)
