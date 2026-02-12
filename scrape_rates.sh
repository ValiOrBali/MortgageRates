#!/usr/bin/bash
source_file="$(dirname $(readlink -f $0))/credit_unions.csv"
curl_output="$(dirname $(readlink -f $0))/curl_output.txt"
wget_output="$(dirname $(readlink -f $0))/credit_units.txt"
headless_search="$(dirname $(readlink -f $0))/headless_search.py"
log_file="$(dirname $(readlink -f $0))/headless_search.log"
base_url="https://mortgages.cumortgage.net/start_up.asp"
siteid_url="https://mortgages.cumortgage.net/default.asp?siteId="
mortgage_rates="$(dirname $(readlink -f $0))/mortgage_rates.csv"

get_mortgage_units()
{
[[ -n start_up.asp ]] && rm -rf start_up.asp*
wget "${base_url}"
[[ -n start_up.asp ]] && cat start_up.asp| grep "option value="| grep -v 'option value="' > "${wget_output}"
for i in $(cat "${wget_output}"  |sed 's/> </>\n</g'|sed 's/<option //g;s/<\/option>//g;s/value=//g;s/ /-/g')
do 
	sid=$(echo "${i}"|cut -d'>' -f1)
	union_name=$(echo "${i}"|cut -d">" -f2|sed 's/-//g'|sed "s/,//g;s/\.//g;s/'//g"|sed 's/\r//g')
	echo "$union_name,$siteid_url$sid"
done 
}

get_mortgage_rates()
{
echo "CreditUnion,Link,Rates(30Years),BestRate"
for single_union in $(cat "${source_file}"|grep -vi best)
do
	rate_output=""
	union_name=$(echo "${single_union}"|cut -d, -f1)
	union_link=$(echo "${single_union}"|cut -d, -f2)
	curl -s $union_link > $curl_output
	while ! grep -q "Today" $curl_output; do
		python3 $headless_search "${union_link}" > $log_file 2>&1
		sleep 2 # Wait for 2 seconds before checking again
 		curl -s $union_link > $curl_output
	done
	output=$(grep 'border="0"' $curl_output  | grep Today | sed 's/></>\n</g' |grep -E "productDetailsSamplePmt|Interest Rate"|sed 's/<\/a>//g;s/<\/td>//g'|rev|cut -d">" -f1|rev|sed 's/ //g'|sed 's/-/|/g' |paste -sd','|sed 's/|/-/g'|sed 's/%,/%|/g;s/,/#/g;s/|/,/g;s/#/|/g')
	if [[ -z "${output}" ]]; then
		output=$(cat $curl_output  | grep Today | sed 's/></>\n</g' |grep -E "productDetailsSamplePmt|Interest Rate"|sed 's/<\/a>//g;s/<\/td>//g'|rev|cut -d">" -f1|rev|sed 's/ //g'|sed 's/-/|/g' |paste -sd','|sed 's/|/-/g'|sed 's/%,/%|/g;s/,/#/g;s/|/,/g;s/#/|/g')	
	fi
	for single_output in $(echo "${output}"|sed 's/,/\n/g')
	do
		mortgage_program=$(echo "${single_output}"|cut -d"|" -f1|sed 's/-Conforming//g;s/-Conforming1//g')
		if [[ $(echo "${mortgage_program}" | grep -viE "20Year|FHA|15Year|30Year|VA|20Yr|15Yr|30Yr|10Yr|10Year|DownPmt") ]]; then
		      interest_rate=$(echo "${single_output}"|cut -d"|" -f2)
	              rate_output+=$mortgage_program-$interest_rate"|" 
                elif [[ $(echo "${mortgage_program}" |grep -vEi "VA|DownPmt"| grep -E "30Year|30Yr") ]]; then 
		      interest_rate=$(echo "${single_output}"|cut -d"|" -f2)
		      rate_output+=$mortgage_program-$interest_rate"|"
		fi
	done
		if [[ -z "${rate_output}" ]]; then
		    rate_output="None"
			best_rate="None"
        	echo "$union_name,$union_link,$rate_output,$best_rate"
		else
			rate_output=$(echo "${rate_output}"|sed 's/.$//g')
			best_rate=$(echo "${rate_output}"|tr '|' '\n' | sort -t'-' -k2,2n|head -1)
			echo "$union_name,$union_link,$rate_output,$best_rate"
		fi
done
}

rm -rf start_up.asp* $log_file $curl_output $source_file $wget_output
get_mortgage_units > "${source_file}"
get_mortgage_rates > "${mortgage_rates}"
rm -rf start_up.asp* $log_file $curl_output $source_file $wget_output