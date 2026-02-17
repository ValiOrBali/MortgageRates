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
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            background-color: #f4f7fa;
            color: #333;
            line-height: 1.6;
        }
        .container {
            max-width: 1200px;
            margin: 30px auto;
            padding: 20px;
            background-color: #fff;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
        }
        h1 {
            color: #2c3e50;
            text-align: center;
            margin-bottom: 30px;
            font-size: 2.2em;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 25px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
            border-radius: 8px;
            overflow: hidden; /* Ensures rounded corners apply to children */
        }
        th, td {
            border: 1px solid #e0e6ed;
            padding: 12px 15px;
            text-align: left;
        }
        th {
            background-color: #4CAF50; /* A pleasant green */
            color: white;
            font-weight: bold;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            font-size: 0.9em;
        }
        tr:nth-child(even) {
            background-color: #f8fcf9; /* Lighter shade for even rows */
        }
        tr:hover {
            background-color: #e8f5e9; /* Light green on hover */
            transition: background-color 0.3s ease;
        }
        a {
            color: #007bff;
            text-decoration: none;
            transition: color 0.3s ease;
        }
        a:hover {
            text-decoration: underline;
            color: #0056b3;
        }
    </style>
</head>
<body>
    <div class="container">
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
