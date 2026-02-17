import csv
import os
import sys
import datetime
import json
import urllib.parse

def convert_csv_to_html(csv_file_path, html_file_path):
    try:
        with open(csv_file_path, mode='r', newline='', encoding='utf-8') as infile:
            reader = csv.reader(infile)
            headers = next(reader) # Get headers
            raw_data = []
            for row in reader:
                raw_data.append(row)

            # Update headers list for internal processing
            if 'Rates(30Years)' in headers:
                rates_column_index = headers.index('Rates(30Years)')
                headers[rates_column_index] = 'Rates' # Rename for consistency

            # Process data to store all rates for each credit union
            processed_credit_unions_data = []
            for row_data in raw_data:
                credit_union_name = row_data[headers.index('CreditUnion')]
                link = row_data[headers.index('Link')]
                rates_raw = row_data[headers.index('Rates')] # Use new header name
                best_rate_overall_raw = row_data[headers.index('BestRate')]

                parsed_rates = []
                if rates_raw != "None":
                    for rate_entry in rates_raw.split('|'):
                        parts = rate_entry.rsplit('-', 1) # Split from right, once
                        if len(parts) == 2:
                            loan_type_full = parts[0].strip()
                            rate_str = parts[1].strip()
                            numeric_rate = None
                            try:
                                numeric_rate = float(rate_str.strip('%'))
                            except ValueError:
                                pass

                            # Determine simplified loan type for filtering and display
                            simplified_type = "Conventional"
                            year_term = None
                            if "ARM" in loan_type_full.upper():
                                simplified_type = "ARM"
                            elif "30 Year Fixed" in loan_type_full:
                                year_term = "30 Years"
                            elif "20 Year Fixed" in loan_type_full:
                                year_term = "20 Years"
                            elif "15 Year Fixed" in loan_type_full:
                                year_term = "15 Years"
                            elif "Jumbo 30 Year Fixed" in loan_type_full:
                                simplified_type = "Jumbo"
                                year_term = "30 Years"
                            elif "Jumbo 15 Year Fixed" in loan_type_full:
                                simplified_type = "Jumbo"
                                year_term = "15 Years"

                            parsed_rates.append({
                                'loanTypeFull': loan_type_full,
                                'rateStr': rate_str,
                                'numericRate': numeric_rate,
                                'simplifiedType': simplified_type,
                                'yearTerm': year_term # Will be None for ARM or other types
                            })

                processed_credit_unions_data.append({
                    'CreditUnion': credit_union_name,
                    'Link': link,
                    'Rates': rates_raw, # Use new header name
                    'BestRateOverall': best_rate_overall_raw, # Keep original best rate
                    'parsedRates': parsed_rates
                })

            # Convert processed data to a URL-encoded JSON string for safe embedding in JS
            json_data_for_js_encoded = urllib.parse.quote(json.dumps(processed_credit_unions_data))

            # Generate HTML content
            html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mortgage Rates</title>
    <style>
        body {{ /* Double curly braces for literal braces in f-string */
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            background-color: #f4f7fa;
            color: #333;
            line-height: 1.6;
        }}
        .container {{
            max-width: 1200px;
            margin: 30px auto;
            padding: 20px;
            background-color: #fff;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
        }}
        h1 {{
            color: #2c3e50;
            text-align: center;
            margin-bottom: 30px;
            font-size: 2.2em;
        }}
        .controls-container {{
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
            gap: 15px;
            margin-bottom: 25px;
        }}
        .search-input, .filter-select {{
            padding: 10px 15px;
            border: 1px solid #ccc;
            border-radius: 5px;
            font-size: 1em;
            box-shadow: inset 0 1px 3px rgba(0,0,0,0.1);
            transition: border-color 0.3s ease;
            width: 100%;
            max-width: 250px;
        }}
        .search-input:focus, .filter-select:focus {{
            border-color: #4CAF50;
            outline: none;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 25px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
            border-radius: 8px;
            overflow: hidden; /* Ensures rounded corners apply to children */
        }}
        th, td {{
            border: 1px solid #e0e6ed;
            padding: 12px 15px;
            text-align: left;
        }}
        th {{
            background-color: #4CAF50; /* A pleasant green */
            color: white;
            font-weight: bold;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            font-size: 0.9em;
            cursor: pointer; /* Indicate sortable */
        }}
        th.sortable:hover {{
            background-color: #3d8f41; /* Darker green on hover for sortable headers */
        }}
        .asc::after {{
            content: ' ▲';
        }}
        .desc::after {{
            content: ' ▼';
        }}
        tr:nth-child(even) {{
            background-color: #f8fcf9; /* Lighter shade for even rows */
        }}
        tr:hover {{
            background-color: #e8f5e9; /* Light green on hover */
            transition: background-color 0.3s ease;
        }}
        a {{
            color: #007bff;
            text-decoration: none;
            transition: color 0.3s ease;
        }}
        a:hover {{
            text-decoration: underline;
            color: #0056b3;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Mortgage Rates</h1>
        <div class="controls-container">
            <input type="text" id="creditUnionSearch" class="search-input" placeholder="Search Credit Union...">
            <select id="loanTypeFilter" class="filter-select">
                <option value="all">All Loan Types</option>
                <option value="arm">ARM</option>
                <option value="conventional30">Conventional (30 Years)</option>
                <option value="conventional20">Conventional (20 Years)</option>
                <option value="conventional15">Conventional (15 Years)</option>
                <option value="jumbo30">Jumbo (30 Years)</option>
                <option value="jumbo15">Jumbo (15 Years)</option>
            </select>
        </div>
        <table id="mortgageRatesTable">
        <thead>
            <tr>
"""
            best_rate_header_index = headers.index('BestRate') if 'BestRate' in headers else -1
            rates_header_index = headers.index('Rates') if 'Rates' in headers else -1

            for i, header_text in enumerate(headers):
                sort_key = header_text.lower().replace(' ', '').replace('(', '').replace(')', '')
                if i == best_rate_header_index:
                    html_content += f"                <th class=\"sortable\" data-sort-key=\"{sort_key}\" id=\"bestRateHeader\">{header_text}</th>\n"
                else:
                    html_content += f"                <th class=\"sortable\" data-sort-key=\"{sort_key}\">{header_text}</th>\n"
            html_content += """            </tr>
        </thead>
        <tbody>
"""
            # Generate table rows using the original raw_data for initial display
            for idx, row_data in enumerate(raw_data):
                html_content += f"            <tr data-row-index=\"{idx}\">\n"
                for i, cell in enumerate(row_data):
                    current_header = headers[i]
                    if current_header == 'Link':
                        html_content += f"                <td><a href=\"{cell}\" target=\"_blank\">{cell}</a></td>\n"
                    elif current_header == 'Rates': # Use new header name
                        formatted_rates = cell.replace('|', '<br>')
                        html_content += f"                <td>{formatted_rates}</td>\n"
                    elif current_header == 'BestRate':
                         # This cell will be updated by JS, initially show original best rate
                        html_content += f"                <td class=\"dynamic-best-rate\">{best_rate_overall_raw}</td>\n"
                    else:
                        html_content += f"                <td>{cell}</td>\n"
                html_content += "            </tr>\n"


            html_content += f"""        </tbody>
    </table>
    <script>
        // Decode and parse the JSON data embedded by Python
        const allCreditUnionsData = JSON.parse(decodeURIComponent("{json_data_for_js_encoded}"));

        document.addEventListener('DOMContentLoaded', function () {{
            const table = document.getElementById('mortgageRatesTable');
            const tbody = table.querySelector('tbody');
            const headers = table.querySelectorAll('th.sortable');
            const creditUnionSearchInput = document.getElementById('creditUnionSearch');
            const loanTypeFilter = document.getElementById('loanTypeFilter');
            const bestRateHeader = document.getElementById('bestRateHeader');

            let sortDirection = {{}};
            let originalRows = Array.from(tbody.querySelectorAll('tr'));

            headers.forEach(header => {{
                const sortKey = header.dataset.sortKey;
                sortDirection[sortKey] = 'asc';
            }});

            headers.forEach(header => {{
                header.addEventListener('click', function () {{
                    const columnIndex = Array.from(header.parentNode.children).indexOf(header);
                    const currentSortKey = header.dataset.sortKey;
                    
                    sortDirection[currentSortKey] = (sortDirection[currentSortKey] === 'asc') ? 'desc' : 'asc';

                    headers.forEach(h => {{
                        h.classList.remove('asc', 'desc');
                    }});
                    header.classList.add(sortDirection[currentSortKey]);

                    sortTable(columnIndex, currentSortKey, sortDirection[currentSortKey]);
                }});
            }});

            function sortTable(columnIndex, sortKey, direction) {{
                let rows = Array.from(tbody.querySelectorAll('tr')).filter(row => row.style.display !== 'none');

                rows.sort((rowA, rowB) => {{
                    let cellA = rowA.children[columnIndex].textContent;
                    let cellB = rowB.children[columnIndex].textContent;

                    if (sortKey === 'bestrate') {{
                        let valA = parseFloat(cellA.replace(/[^\\d.]/g, '')) || Infinity;
                        let valB = parseFloat(cellB.replace(/[^\\d.]/g, '')) || Infinity;

                        if (direction === 'asc') {{
                            return valA - valB;
                        }} else {{
                            return valB - valA;
                        }}
                    }}
                    else {{
                        if (direction === 'asc') {{
                            return cellA.localeCompare(cellB);
                        }} else {{
                            return cellB.localeCompare(cellA);
                        }}
                    }}
                }});

                tbody.innerHTML = '';
                rows.forEach(row => tbody.appendChild(row));
            }}

            function applyFilters() {{
                const selectedLoanType = loanTypeFilter.value;
                const creditUnionSearchTerm = creditUnionSearchInput.value.toLowerCase();
                const bestRateColumnIndex = Array.from(table.querySelectorAll('th')).findIndex(th => th.dataset.sortKey === 'bestrate');

                // Update BestRate header text - Fixed to 30 Years Only
                bestRateHeader.textContent = "BESTRATE (30 YEARS ONLY)";


                originalRows.forEach(row => {{
                    const rowIndex = parseInt(row.dataset.rowIndex);
                    const creditUnionData = allCreditUnionsData[rowIndex];
                    const creditUnionName = creditUnionData['CreditUnion'].toLowerCase();
                    const rates = creditUnionData.parsedRates;

                    let showRow = true;
                    let currentBestRate = "None";
                    let minRateValue = Infinity;

                    if (!creditUnionName.includes(creditUnionSearchTerm)) {{
                        showRow = false;
                    }}

                    if (showRow) {{
                        let applicableRates = [];
                        
                        // Always find the best 30-year rate for the BestRate column
                        for (const rate of rates) {{
                            // Filter for 30 Year Conventional or 30 Year Jumbo
                            if (rate.yearTerm === "30 Years" && 
                                (rate.simplifiedType === "Conventional" || rate.simplifiedType === "Jumbo")) {{
                                applicableRates.push(rate);
                            }}
                        }}

                        if (applicableRates.length > 0) {{
                            let bestApplicableRate = null;
                            for (const rate of applicableRates) {{
                                if (rate.numericRate !== null && rate.numericRate < minRateValue) {{
                                    minRateValue = rate.numericRate;
                                    bestApplicableRate = rate;
                                }}
                            }}
                            if (bestApplicableRate) {{
                                currentBestRate = `${{bestApplicableRate.loanTypeFull}}-${{bestApplicableRate.rateStr}}`;
                            }}
                        }}

                        // Now, re-evaluate showRow based on the selectedLoanType filter for actual row visibility
                        let meetsLoanTypeFilter = false;
                        if (selectedLoanType === "all") {{
                            meetsLoanTypeFilter = true;
                        }} else {{
                            for (const rate of rates) {{
                                if (selectedLoanType === "arm" && rate.simplifiedType === "ARM") {{
                                    meetsLoanTypeFilter = true;
                                    break;
                                }} else if (selectedLoanType === "conventional30" && rate.yearTerm === "30 Years" && rate.simplifiedType === "Conventional") {{
                                    meetsLoanTypeFilter = true;
                                    break;
                                }} else if (selectedLoanType === "conventional20" && rate.yearTerm === "20 Years" && rate.simplifiedType === "Conventional") {{
                                    meetsLoanTypeFilter = true;
                                    break;
                                }} else if (selectedLoanType === "conventional15" && rate.yearTerm === "15 Years" && rate.simplifiedType === "Conventional") {{
                                    meetsLoanTypeFilter = true;
                                    break;
                                }} else if (selectedLoanType === "jumbo30" && rate.yearTerm === "30 Years" && rate.simplifiedType === "Jumbo") {{
                                    meetsLoanTypeFilter = true;
                                    break;
                                }} else if (selectedLoanType === "jumbo15" && rate.yearTerm === "15 Years" && rate.simplifiedType === "Jumbo") {{
                                    meetsLoanTypeFilter = true;
                                    break;
                                }}
                            }}
                        }}
                        showRow = showRow && meetsLoanTypeFilter;
                    }}

                    if (bestRateColumnIndex !== -1) {{
                        const bestRateCell = row.children[bestRateColumnIndex];
                        if (bestRateCell) {{
                            bestRateCell.textContent = currentBestRate;
                        }}
                    }}

                    row.style.display = showRow ? '' : 'none';
                }});
                const currentlySortedHeader = table.querySelector('th.asc, th.desc');
                if (currentlySortedHeader) {{
                    const columnIndex = Array.from(currentlySortedHeader.parentNode.children).indexOf(currentlySortedHeader);
                    const currentSortKey = currentlySortedHeader.dataset.sortKey;
                    const currentDirection = currentlySortedHeader.classList.contains('asc') ? 'asc' : 'desc';
                    sortTable(columnIndex, currentSortKey, currentDirection);
                }}

            }}

            loanTypeFilter.addEventListener('change', applyFilters);
            creditUnionSearchInput.addEventListener('keyup', applyFilters);
            applyFilters();
        }});
    </script>
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
