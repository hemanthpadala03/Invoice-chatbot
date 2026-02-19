import pandas as pd
import os


from langchain_experimental.agents import create_pandas_dataframe_agent
from langchain_ollama import OllamaLLM
from langchain_classic.memory import ConversationBufferWindowMemory  
from langsmith import traceable
file_invoices = r"C:\Drive_d\Python\F-AI\T8\data\master_invoices.csv"
file_items = r"C:\Drive_d\Python\F-AI\T8\data\master_items.csv"

df_invoices = pd.read_csv(file_invoices)
df_items = pd.read_csv(file_items)


# Clean numeric data
# if "TotalAmount" in df_items.columns:
#     df_items["TotalAmount"] = pd.to_numeric(df_items["TotalAmount"], errors="coerce").fillna(0)

# =====================================================
# 2. AGENT SETUP (Mistral)
# =====================================================
llm = OllamaLLM(model="mistral", temperature=0)

PREFIX = """
You are a expert data analyst. who can answer simple questions like hi, hello, who are you directly as a invoice assistant 
for remaining You have two dataframes:
df2 (Items): ['Description', 'TotalAmount', 'Source_File', 'Qty', 'UnitPrice']
df1 (Metadata): ['Field', 'Value', 'source', 'file_name']

----------------------------------------------------
DATAFRAME df2: Item Details (columns)
----------------------------------------------------
Columns: ['SlNo', 'Description', 'UnitPrice', 'Qty','TaxAmount','TaxRate','TotalAmount', 'Source_File']
here source file names include which brand(file names) they belong to (e.g., Amazon 1.xlsx, Amazon 2.xlsx, Blinkit 1.xlsx, etc.)
----------------------------------------------------
FIELD NAMES inside the Field column IN df1 (Metadata):
----------------------------------------------------
'billing_address', 'shipping_address', 'invoice_type', 'order_number', 
'invoice_number', 'order_date', 'invoice_date', 'invoice_details', 
'seller_info', 'seller_name', 'seller_address', 'seller_gstin', 
'pan_number', 'total_tax', 'total_amount', 'subtotal'

----------------------------------------------------
STRICT OPERATIONAL RULES:
----------------------------------------------------
1. SEARCHING PRODUCTS: NEVER use `==`. ALWAYS use `.str.contains('keyword', case=False, na=False)`.
2. PANDAS SYNTAX: Always use standard pandas indexing. Use parentheses for multiple conditions: (df['A'] == x) & (df['B'] == y).
3. PLATFORM TOTALS: Platform names (Amazon, Blinkit) are in the 'Source_File' column of df2. 
4. CROSS-REFERENCING (The "Shipping Address" Logic):
   - Step 1: Find the item in df2 using .str.contains().
   - Step 2: Extract the 'Source_File' value from that result.
   - Step 3: Filter df1 where (df1['file_name'] == 'Extracted_Source_File') & (df1['Field'] == 'shipping_address').
5. SINGLE DF USE: Even If a question is a bit related to amount or tax or count, only use df2. Only use df1 if metadata (address, PAN, date, gst) is requested.
6. COUNTING: Use `len(df2[condition])` to count items.
7. ERROR HANDLING: If a query cannot be answered with the data, respond with "Sorry, I don't have that information."
8. NO NUMPY ACCESS: NEVER use `[:,3]`. Use column names like `df['Source_File']`.
9. NEVER include Thought, Action, Action Input, or raw pandas code in the final answer.
10. The final answer must contain ONLY the final user-facing answer.
11. Do NOT repeat the tool output. Only summarize the result clearly.
"""
# ================================
# MEMORY STORES
# ================================
memory_store = {}
agent_store = {}

WINDOW_SIZE = 3   # last 6 interactions only

@traceable
def get_memory(session_id):
    """
    Session memory used ONLY for model context.
    Not full chat history.
    """
    if session_id not in memory_store:
        memory_store[session_id] = ConversationBufferWindowMemory(
            memory_key="chat_history",
            return_messages=True,
            k=WINDOW_SIZE
        )
    return memory_store[session_id]

@traceable
def get_agent(session_id):

    if session_id in agent_store:
        return agent_store[session_id]

    memory = get_memory(session_id)

    agent = create_pandas_dataframe_agent(
        llm,
        [df_invoices, df_items],
        prefix=PREFIX,
        memory=memory,
        verbose=True,
        allow_dangerous_code=True,
        max_iterations=6,
        include_df_in_prompt=True,
        agent_executor_kwargs={
            "handle_parsing_errors": True,
        }
    )

    agent_store[session_id] = agent
    return agent

@traceable
def ask_agent(user_query: str, session_id: str):


    agent = get_agent(session_id)
    response = agent.invoke({"input": user_query})

    return response["output"]