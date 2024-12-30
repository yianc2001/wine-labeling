# Import necessary libraries
import pandas as pd
import openai
import csv

# Initialize constants and variables
knowledge_path = "info/knowledge.txt"
demo_path = "info/demo.txt"
example_path = "info/example.txt"
output_csv = "output/labels.csv"
output_txt = "output/labels.txt"
MY_KEY = "" 
openai.api_key = MY_KEY
category_list = ["產區標籤", "國家標籤", "品種標籤", "風味標籤", "口感標籤", "製成標籤"]
ADD_CATEGORY = True

# Define functions
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

def suggest_new_categories(knowledge, category_list):
    """Ask AI for new categories based on knowledge."""
    prompt = (
            f"目前的標籤類別包括：\n\n{', '.join(category_list)}\n\n"
            f"以下是關於葡萄酒的專業知識：\n\n{knowledge}\n\n"
            "為了達到從各種角度去描述葡萄酒的目的，請根據以上內容建議新的標籤類別。"
    )
    response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200
    )
    suggested_categories = response["choices"][0]["message"]["content"].split("\n")
    category_list.extend([cat.strip() for cat in suggested_categories if cat.strip() and cat not in category_list])

    return response["choices"][0]["message"]["content"].split("\n")

def determine_reference_and_number(knowledge, category):
    """
    Determine the reference type and the target number of labels for a given category.
    
    Parameters:
    - knowledge (str): The background knowledge to be provided to the AI.
    - category (str): The current label category.

    Returns:
    - tuple: A tuple containing the reference type (str) and the target number of labels (int).
    """
    prompt = (
        f"以下是關於葡萄酒的知識：\n\n{knowledge}\n\n"
        f"請針對目前的標籤類別「{category}」決定參考資料應該為何者？\n"
        "適合參考專業知識，回傳:專業知識；適合參考酒款文案，回傳:酒款文案；"
        "兩者皆要參考，回傳:All。\n"
        "請決定該類標籤需生成多少之數量？\n"
        "格式請回傳如下：\n"
        "(第一行)參考資料\n"
        "(第二行)目標數量"
    )

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=100
        )
        result = response["choices"][0]["message"]["content"].strip()
        
        # Split response into lines
        lines = result.split("\n")
        if len(lines) != 2:
            raise ValueError("Invalid response format: Expected two lines")
        
        # Extract reference and number
        reference = lines[0].strip()
        try:
            target_number = int(lines[1].strip())
        except ValueError:
            raise ValueError("Invalid target number: Expected an integer on the second line")
        
        # Validate reference
        if reference not in ["專業知識", "酒款文案", "All"]:
            raise ValueError("Invalid reference type: Must be 專業知識, 酒款文案, or All")
        
        return reference, target_number
    
    except Exception as e:
        raise RuntimeError(f"Error in determining reference and number: {e}")


def generate_labels(knowledge, examples, category, num_labels):
    """Generate labels using AI based on knowledge and examples."""
    prompt = f"以下是關於葡萄酒的知識：\n\n{knowledge}\n\n和範例標籤：\n\n{examples}\n\n請根據以上內容為「{category}」生成至少 {num_labels} 個創意標籤。"
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=500
    )
    return response["choices"][0]["message"]["content"].split("\n")

def save_to_csv(category, labels, output_path):
    """Save labels to CSV."""
    with open(output_path, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        for label in labels:
            writer.writerow([category, label])

def save_to_txt(input_csv, output_txt):
    """Extract labels column from CSV and save to TXT."""
    labels = []
    with open(input_csv, mode="r", encoding="utf-8") as file:
        reader = csv.reader(file)
        labels = [row[1] for row in reader]  # Assume second column is the label
    with open(output_txt, mode="w", encoding="utf-8") as file:
        file.write("\n".join(labels))

# Main
def main():
    knowledge_content = read_file(knowledge_path)
    demo_content = read_file(demo_path)
    example_content = read_file(example_path)

    categories = category_list
    if ADD_CATEGORY:
        new_categories = suggest_new_categories(knowledge_content, category_list)
    categories.extend(new_categories)

    for category in categories:
        print(f"Processing category: {category}")
        reference, num_labels = determine_reference_and_number(knowledge_content, category)
        
        if reference == "專業知識":
            ref_knowledge = knowledge_content
        elif reference == "酒款文案":
            ref_knowledge = demo_content
        elif reference == "ALL":
            ref_knowledge = knowledge_content + "\n" + demo_content
        else:
            raise ValueError("Invalid reference type")
        
        labels = generate_labels(ref_knowledge, example_content, category, num_labels)

        save_to_csv(category, labels, output_csv)
        print(f"Labels of category {category} have been generated successfully.")
    
    # Save all labels to TXT
    save_to_txt(output_csv, output_txt)
    print("Workflow completed!")

if __name__ == "__main__":
    main()
