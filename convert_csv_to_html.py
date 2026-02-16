import csv
import os
import sys

def convert_csv_to_html(csv_file_path, html_file_path):
    try:
        with open(csv_file_path, mode='r', newline='', encoding='utf-8') as infile:
            reader = csv.reader(infile)
            headers = next(reader) # Get headers

            html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mortgage Rates</title>
    <style>
        body { font-family: sans-serif; margin: 20px; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
        tr:nth-child(even) { background-color: #f9f9f9; }
        a { color: #007bff; text-decoration: none; }
        a:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <h1>Mortgage Rates</h1>
    <table>
        <thead>
            <tr>
"""
            for header in headers:
                html_content += f"                <th>{header}</th>\n"
            html_content += """            </tr>
        </thead>
        <tbody>
"""
            for row in reader:
                html_content += "            <tr>\n"
                for i, cell in enumerate(row):
                    if headers[i] == 'Link': # Make the Link column clickable
                        html_content += f"                <td><a href=\"{cell}\" target=\"_blank\">{cell}</a></td>\n"
                    elif headers[i] == 'Rates(30Years)': # Format Rates(30Years) to be more readable
                        formatted_rates = cell.replace('|', '<br>')
                        html_content += f"                <td>{formatted_rates}</td>\n"
                    else:
                        html_content += f"                <td>{cell}</td>\n"
                html_content += "            </tr>\n"

            html_content += """        </tbody>
    </table>
</body>
</html>"""

        with open(html_file_path, mode='w', encoding='utf-8') as outfile:
            outfile.write(html_content)
        print(f"Successfully converted '{csv_file_path}' to '{html_file_path}'")
    except FileNotFoundError:
        print(f"Error: The file '{csv_file_path}' was not found.", file=sys.stderr)
    except Exception as e:
        print(f"An error occurred: {e}", file=sys.stderr)

if __name__ == "__main__":
    script_dir = os.path.dirname(__file__)
    csv_input_path = os.path.join(script_dir, "mortgage_rates.csv")
    html_output_path = os.path.join(script_dir, "mortgage_rates.html")
    
    convert_csv_to_html(csv_input_path, html_output_path)
