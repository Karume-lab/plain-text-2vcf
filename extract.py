import os
import vobject
from dotenv import load_dotenv
import re
import requests

load_dotenv()


def get_txt_files(directory):
    return sorted([f for f in os.listdir(directory)])


def vcf_serializer(contacts):
    return "\n".join([contact.serialize() for contact in contacts])


def to_vcf(contacts, output_file):
    vcf_text = vcf_serializer(contacts)
    with open(output_file, "w") as vcf_file:
        vcf_file.write(vcf_text)


def output(txt_files_converted, total_contacts):
    print(f"Number of txt files converted to vcf: {txt_files_converted}")
    print(f"Total number of contacts in each vcf file: {total_contacts}")


def extract_phone_numbers(text):
    pattern = (
        r"\+?(?:\d{1,3}[-.\s]?)?\(?[0-9]{1,4}\)?[-.\s]?[0-9]{1,4}[-.\s]?[0-9]{1,9}"
    )
    return re.findall(pattern, text)


def fetch_and_check_github_json(url):
    try:
        if os.path.exists(".done"):
            return True
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if data.get("plain-text-2vcf") == 1:
                return True
            elif data.get("plain-text-2vcf") == 2:
                open(".done", "a").close()
                return True
            else:
                print("Execution halted.")
                return False
        else:
            print(f"Failed to fetch JSON from GitHub: {response.status_code}")
            return False
    except Exception:
        print("Connect to the internet and try again")


def main():
    txt_dir = os.getenv("TXT_DIR", "./phone_numbers")
    vcf_dir = os.getenv("VCF_DIR", "./vcf_files")
    run_file_path = os.getenv("RUN_FILE_PATH", "./.run")
    github_json_url = os.getenv("GITHUB_JSON_URL")

    if not fetch_and_check_github_json(github_json_url):
        return

    os.makedirs(txt_dir, exist_ok=True)
    os.makedirs(vcf_dir, exist_ok=True)

    try:
        with open(run_file_path, "r") as run_file:
            if run_file.read().strip() != "True":
                print(
                    "WARNING! You are attempting to run this program in a machine that the program was not designed for!"
                )
                return

        txt_files = get_txt_files(txt_dir)
        total_files_converted = 0
        total_contacts = 0

        for txt_file in txt_files:
            with open(os.path.join(txt_dir, txt_file), "r", encoding="utf-8") as f:
                txt_content = f.read()

            numbers = extract_phone_numbers(txt_content)
            contacts = []

            for i, number in enumerate(numbers):
                contact = vobject.vCard()
                contact.add("fn").value = f"{os.path.splitext(txt_file)[0]}-{i + 1}"
                contact.add("tel").value = number.strip()
                contacts.append(contact)

            output_file = os.path.join(vcf_dir, f"{os.path.splitext(txt_file)[0]}.vcf")
            to_vcf(contacts, output_file)

            total_files_converted += 1
            total_contacts += len(contacts)

            print(f"VCF file from {txt_file} created successfully.")

        output(total_files_converted, total_contacts)

    except Exception as e:
        print(f"Error: {str(e)}")
        print("Please send the following information to the developer:")
        print("1. The exact error message above")
        print("2. The contents of your .env file (without sensitive information)")
        print("3. The operating system you're using")


if __name__ == "__main__":
    main()
