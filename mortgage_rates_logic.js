document.addEventListener('DOMContentLoaded', function () {
    const table = document.getElementById('mortgageRatesTable');
    const tbody = table.querySelector('tbody');
    const headers = table.querySelectorAll('th.sortable');
    const creditUnionSearchInput = document.getElementById('creditUnionSearch');
    const loanTypeFilter = document.getElementById('loanTypeFilter');
    const bestRateHeader = document.getElementById('bestRateHeader');
    const bestProgram30yrHeader = document.getElementById('bestProgram30yrHeader'); 

    let sortDirection = {};
    let originalRows = [];

    // Populate table body and store original rows
    allCreditUnionsData.forEach((creditUnionData, index) => {
        let row = tbody.insertRow();
        row.dataset.rowIndex = index;

        let creditUnionCell = row.insertCell();
        creditUnionCell.textContent = creditUnionData['CreditUnion'];

        let linkCell = row.insertCell();
        let linkAnchor = document.createElement('a');
        linkAnchor.href = creditUnionData['Link'];
        linkAnchor.target = '_blank';
        linkAnchor.textContent = creditUnionData['Link'];
        linkCell.appendChild(linkAnchor);

        // Programs column (now a nested table)
        let programsCell = row.insertCell();
        let programsTableHtml = '<table class="program-table"><thead><tr><th>Program</th><th>Interest Rate</th></tr></thead><tbody>';
        creditUnionData.parsedRates.forEach(rate => {
            if (rate.loanTypeFull && rate.rateStr) {
                programsTableHtml += `<tr><td>${rate.loanTypeFull}</td><td>${rate.rateStr}</td></tr>`;
            }
        });
        programsTableHtml += '</tbody></table>';
        programsCell.innerHTML = programsTableHtml;

        // Best Program (30 Year) column 
        let bestProgram30yrCell = row.insertCell();
        bestProgram30yrCell.classList.add('dynamic-best-program-30yr');
        bestProgram30yrCell.textContent = "None"; 

        // Best Rate column 
        let bestRateCell = row.insertCell();
        bestRateCell.classList.add('dynamic-best-rate');
        bestRateCell.textContent = "None"; 
        
        originalRows.push(row);
    });


    headers.forEach(header => {
        const sortKey = header.dataset.sortKey;
        sortDirection[sortKey] = 'asc';
    });

    headers.forEach(header => {
        header.addEventListener('click', function () {
            const columnIndex = Array.from(header.parentNode.children).indexOf(header);
            const currentSortKey = header.dataset.sortKey;
            
            sortDirection[currentSortKey] = (sortDirection[currentSortKey] === 'asc') ? 'desc' : 'asc';

            headers.forEach(h => {
                h.classList.remove('asc', 'desc');
            });
            header.classList.add(sortDirection[currentSortKey]);

            sortTable(columnIndex, currentSortKey, sortDirection[currentSortKey]);
        });
    });

    function sortTable(columnIndex, sortKey, direction) {
        let rows = Array.from(tbody.children).filter(row => row.style.display !== 'none'); // FIXED: Use tbody.children

        rows.sort((rowA, rowB) => {
            let cellA = rowA.children[columnIndex].textContent;
            let cellB = rowB.children[columnIndex].textContent;

            if (sortKey === 'bestrate') {
                let valA = parseFloat(cellA.replace(/[^\\d.]/g, ''));
                let valB = parseFloat(cellB.replace(/[^\\d.]/g, ''));

                // Treat "None" or NaN as a very large number for sorting purposes
                valA = isNaN(valA) ? Infinity : valA;
                valB = isNaN(valB) ? Infinity : valB;

                if (direction === 'asc') {
                    return valA - valB;
                } else {
                    return valB - valA;
                }
            } else if (sortKey === 'bestprogram30yr') {
                // Sort alphabetically for program names
                return direction === 'asc' ? cellA.localeCompare(cellB) : cellB.localeCompare(cellA);
            } else {
                // Default alphabetical sort for other columns
                return direction === 'asc' ? cellA.localeCompare(cellB) : cellB.localeCompare(cellA);
            }
        });

        tbody.innerHTML = '';
        rows.forEach(row => tbody.appendChild(row));
    }

    function applyFilters() {
        const selectedLoanType = loanTypeFilter.value;
        const creditUnionSearchTerm = creditUnionSearchInput.value.toLowerCase();
        const bestRateColumnIndex = Array.from(table.querySelectorAll('th')).findIndex(th => th.dataset.sortKey === 'bestrate');
        const bestProgram30yrColumnIndex = Array.from(table.querySelectorAll('th')).findIndex(th => th.dataset.sortKey === 'bestprogram30yr'); 


        if (selectedLoanType === "all") {
            bestRateHeader.textContent = "BEST RATE";
            bestProgram30yrHeader.textContent = "OVERALL BEST PROGRAM"; 
        } else if (selectedLoanType === "arm") {
            bestRateHeader.textContent = "BEST ARM RATE";
            bestProgram30yrHeader.textContent = "BEST ARM PROGRAM";
        } else if (selectedLoanType === "conventional30") {
            bestRateHeader.textContent = "BEST 30YR CONV FIXED RATE";
            bestProgram30yrHeader.textContent = "BEST 30YR CONV FIXED PROGRAM";
        } else if (selectedLoanType === "conventional20") {
            bestRateHeader.textContent = "BEST 20YR CONV FIXED RATE";
            bestProgram30yrHeader.textContent = "BEST 20YR CONV FIXED PROGRAM";
        } else if (selectedLoanType === "conventional15") {
            bestRateHeader.textContent = "BEST 15YR CONV FIXED RATE";
            bestProgram30yrHeader.textContent = "BEST 15YR CONV FIXED PROGRAM";
        } else if (selectedLoanType === "jumbo30") {
            bestRateHeader.textContent = "BEST 30YR JUMBO FIXED RATE";
            bestProgram30yrHeader.textContent = "BEST 30YR JUMBO FIXED PROGRAM";
        } else if (selectedLoanType === "jumbo15") {
            bestRateHeader.textContent = "BEST 15YR JUMBO FIXED RATE";
            bestProgram30yrHeader.textContent = "BEST 15YR JUMBO FIXED PROGRAM";
        } else {
            bestRateHeader.textContent = "BEST RATE"; 
            bestProgram30yrHeader.textContent = "BEST PROGRAM"; 
        }


        originalRows.forEach(row => {
            const rowIndex = parseInt(row.dataset.rowIndex);
            const creditUnionData = allCreditUnionsData[rowIndex];
            const creditUnionName = creditUnionData['CreditUnion'].toLowerCase();
            const rates = creditUnionData.parsedRates;

            let showRow = true;
            let currentBestRateDisplay = "None"; 
            let currentBestProgramDisplay = "None"; 

            let minRateValue = Infinity;
            let bestApplicableRate = null;


            if (!creditUnionName.includes(creditUnionSearchTerm)) {
                showRow = false;
            }

            if (showRow) {
                if (selectedLoanType === "all") {
                    for (const rate of rates) {
                        if (rate.numericRate !== null && rate.numericRate < minRateValue) {
                            minRateValue = rate.numericRate;
                            bestApplicableRate = rate;
                        }
                    }
                } else if (selectedLoanType === "arm") {
                    for (const rate of rates) {
                        if (rate.numericRate !== null && rate.simplifiedType === "ARM") {
                            if (rate.numericRate < minRateValue) {
                                minRateValue = rate.numericRate;
                                bestApplicableRate = rate;
                            }
                        }
                    }
                } else if (selectedLoanType === "conventional30") {
                     for (const rate of rates) {
                        if (rate.numericRate !== null && rate.yearTerm === "30 Years" && rate.simplifiedType === "Conventional" && !rate.loanTypeFull.includes("ARM")) {
                            if (rate.numericRate < minRateValue) {
                                minRateValue = rate.numericRate;
                                bestApplicableRate = rate;
                            }
                        }
                    }
                } else if (selectedLoanType === "conventional20") {
                     for (const rate of rates) {
                        if (rate.numericRate !== null && rate.yearTerm === "20 Years" && rate.simplifiedType === "Conventional" && !rate.loanTypeFull.includes("ARM")) {
                            if (rate.numericRate < minRateValue) {
                                minRateValue = rate.numericRate;
                                bestApplicableRate = rate;
                            }
                        }
                    }
                } else if (selectedLoanType === "conventional15") {
                     for (const rate of rates) {
                        if (rate.numericRate !== null && rate.yearTerm === "15 Years" && rate.simplifiedType === "Conventional" && !rate.loanTypeFull.includes("ARM")) {
                            if (rate.numericRate < minRateValue) {
                                minRateValue = rate.numericRate;
                                bestApplicableRate = rate;
                            }
                        }
                    }
                } else if (selectedLoanType === "jumbo30") {
                     for (const rate of rates) {
                        if (rate.numericRate !== null && rate.yearTerm === "30 Years" && rate.simplifiedType === "Jumbo" && !rate.loanTypeFull.includes("ARM")) {
                            if (rate.numericRate < minRateValue) {
                                minRateValue = rate.numericRate;
                                bestApplicableRate = rate;
                            }
                        }
                    }
                } else if (selectedLoanType === "jumbo15") {
                     for (const rate of rates) {
                        if (rate.numericRate !== null && rate.yearTerm === "15 Years" && rate.simplifiedType === "Jumbo" && !rate.loanTypeFull.includes("ARM")) {
                            if (rate.numericRate < minRateValue) {
                                minRateValue = rate.numericRate;
                                bestApplicableRate = rate;
                            }
                        }
                    }
                }


                if (bestApplicableRate) {
                    currentBestRateDisplay = `${bestApplicableRate.rateStr}`; 
                    currentBestProgramDisplay = `${bestApplicableRate.loanTypeFull}`; 
                }
            }

            let meetsLoanTypeFilter = false;
            if (selectedLoanType === "all") {
                meetsLoanTypeFilter = true;
            } else {
                for (const rate of rates) {
                    if (selectedLoanType === "arm" && rate.simplifiedType === "ARM") {
                        meetsLoanTypeFilter = true;
                        break;
                    } else if (selectedLoanType === "conventional30" && rate.yearTerm === "30 Years" && rate.simplifiedType === "Conventional") {
                        meetsLoanTypeFilter = true;
                        break;
                    } else if (selectedLoanType === "conventional20" && rate.yearTerm === "20 Years" && rate.simplifiedType === "Conventional") {
                        meetsLoanTypeFilter = true;
                        break;
                    } else if (selectedLoanType === "conventional15" && rate.yearTerm === "15 Years" && rate.simplifiedType === "Conventional") {
                        meetsLoanTypeFilter = true;
                        break;
                    } else if (selectedLoanType === "jumbo30" && rate.yearTerm === "30 Years" && rate.simplifiedType === "Jumbo") {
                        meetsLoanTypeFilter = true;
                        break;
                    } else if (selectedLoanType === "jumbo15" && rate.yearTerm === "15 Years" && rate.simplifiedType === "Jumbo") {
                        meetsLoanTypeFilter = true;
                        break;
                    }
                }
            }
            showRow = showRow && meetsLoanTypeFilter;

            if (bestRateColumnIndex !== -1) {
                const bestRateCell = row.children[bestRateColumnIndex];
                if (bestRateCell) {
                    bestRateCell.textContent = currentBestRateDisplay; 
                }
            }
            if (bestProgram30yrColumnIndex !== -1) { 
                const bestProgram30yrCell = row.children[bestProgram30yrColumnIndex];
                if (bestProgram30yrCell) {
                    bestProgram30yrCell.textContent = currentBestProgramDisplay;
                }
            }

            row.style.display = showRow ? '' : 'none';
        });
        const currentlySortedHeader = table.querySelector('th.asc, th.desc');
        if (currentlySortedHeader) {
            const columnIndex = Array.from(currentlySortedHeader.parentNode.children).indexOf(currentlySortedHeader);
            const currentSortKey = currentlySortedHeader.dataset.sortKey;
            const currentDirection = currentlySortedHeader.classList.contains('asc') ? 'asc' : 'desc';
            sortTable(columnIndex, currentSortKey, currentDirection);
        }

    }

    loanTypeFilter.addEventListener('change', applyFilters);
    creditUnionSearchInput.addEventListener('keyup', applyFilters);
    applyFilters();
});
