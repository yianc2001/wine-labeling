import requests
import pandas as pd
import openai

MY_KEY = "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"
openai.api_key = MY_KEY

def read_file(file_path):
    """Read content from Excel or text file."""
    if file_path.endswith(".xlsx"):
        df = pd.read_excel(file_path)
        return df.to_string(index=False)
    elif file_path.endswith(".txt"):
        with open(file_path, "r", encoding="utf-8") as file:
            return file.read()
    else:
        raise ValueError("Unsupported file format")

def revise_text(raw_text):
    """Send a request to OpenAI to revise the text."""
    # Ensure raw_text is safe for inclusion in an f-string
    sanitized_text = raw_text.replace("\\", "\\\\")  # Escape backslashes
    sanitized_text = sanitized_text.replace('"', '\\"')  # Escape double quotes if necessary

    # Construct the prompt
    prompt = (
        f"以下是一些酒款行銷文本：\n\n"
        f"{sanitized_text}\n\n"
        "請對上述文本進行修改，使其成為更適合的「為葡萄酒生成標籤」的參考資料。\n"
    )

    data = {
        "model": "gpt-4",
        "messages": [
            {"role": "system", "content": "你是一位專業的葡萄酒專家，擅長修改文本以便用於生成葡萄酒標籤。"},
            {"role": "user", "content": prompt}
        ]
    }

    try:
        # Send the POST request to OpenAI
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {MY_KEY}"},
            json=data
        )
        
        # Handle the response
        if response.status_code == 200:
            response_data = response.json()
            return response_data['choices'][0]['message']['content'].strip()
        else:
            print(f"Request failed with status {response.status_code}: {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        return None




def choose_example(file_path, n=10):
    """Request OpenAI to choose n good example labels from the raw examples."""
    # Read and sanitize the raw examples
    raw_examples = read_file(file_path).split("\n")
    sanitized_examples = [example.replace("\\", "\\\\").replace('"', '\\"') for example in raw_examples]
    examples_text = "\n".join(sanitized_examples)

    # Construct the prompt
    prompt = (
        f"以下是一些葡萄酒標籤的範例：\n\n"
        f"{examples_text}\n\n"
        f"請從上述範例中選擇最好的 {n} 個標籤。選擇的標籤盡量代表各種類標籤。\n"
    )

    data = {
        "model": "gpt-4",
        "messages": [
            {"role": "system", "content": "你是一位專業的葡萄酒標籤評估專家。"},
            {"role": "user", "content": prompt}
        ]
    }

    try:
        # Send the POST request to OpenAI
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {MY_KEY}"},
            json=data
        )
        
        # Handle the response
        if response.status_code == 200:
            response_data = response.json()
            result = response_data['choices'][0]['message']['content']
            # Split and clean the response to get the chosen examples
            return [label.strip() for label in result.split("\n") if label.strip()][:n]
        else:
            print(f"Request failed with status {response.status_code}: {response.text}")
            return [None] * n
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        return [None] * n


def save_to_file(file_path, content):
    """Save the content to a text file."""
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(content)
    print(f"Content saved to {file_path}")

# Example usage:
raw_text_path = "raw/demo_raw.txt"
raw_example_path = "raw/example_raw.txt"

# Read the raw text from the file
raw_text = read_file(raw_text_path)
print("Raw text:")
print(raw_text[:200])

# Revise the text using OpenAI
revised_text = revise_text(raw_text)
if revised_text:
    print("\nRevised text:")
    print(revised_text[:200])
    save_to_file("info/demo.txt", revised_text)

# Choose the best examples from the raw examples
chosen_examples = choose_example(raw_example_path, n=10)
if chosen_examples:
    print("\nChosen examples:")
    print(chosen_examples)
    save_to_file("info/example.txt", "\n".join(chosen_examples))
