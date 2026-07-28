#!/usr/bin/bash

## -E  # ERR traps are inherited by functions and subshells
## -e  # exit when an unhandled command fails
## -u  # error on unset variables
## -o pipefail  # a pipeline fails if any command in it fails
#set -Eeuo pipefail

############################################################################
##
## - Opening Suppliers > Shipment > Search
##   - APP URL:
##     https://supplier.uat1.ligentix.net/shipments/search
##   - ✅ Get customers
##     GET https://supplier.uat1.ligentix.net/Api/Shipments/bookingSearch/customers
##   - ✅ Get POLs
##     GET https://supplier.uat1.ligentix.net/Api/Shipments/bookingSearch/pols
##   - ✅ Get vessel names
##     GET https://supplier.uat1.ligentix.net/Api/Shipments/bookingSearch/vesselNames
##   - ✅ Get delivery modes
##     GET https://supplier.uat1.ligentix.net/Api/Shipments/bookingSearch/deliveryModes
##   - ✅ Search booking order by shipment number
##     GET https://supplier.uat1.ligentix.net/Api/Shipments/shipmentSearch/shipment
##     query params:
##     - default: 
##       ?pageNumber=1&itemsPerPage=10&orderByFieldName=etd&orderByDirection=asc
##     - by shipment ref:
##       ??pageNumber=1&itemsPerPage=100&cwRefSearchTerm=S01863302&orderByFieldName=etd&orderByDirection=asc
##    - When entering search criteria
##      - Get suppliers
##        ✅ GET https://supplier.uat1.ligentix.net/Api/Shipments/bookingSearch/suppliers
##               ?searchTerm=argion&maxResults=3 (without this return all suppliers)
##
## - Opening a booking, e.g. SE0612240084
##   - App URL: 
##     https://supplier.uat1.ligentix.net/shipments/container-stuffing/Sea/FCL/SE0612240084
##   - Invoke GET
##     https://supplier.uat1.ligentix.net/Api/Shipments/bookingSearch/SE0612240084
##     https://supplier.uat1.ligentix.net/Api/Shipments/shipment/Details/SE0612240084
##     https://supplier.uat1.ligentix.net/Api/Shipments/shipment/SummaryInformation/SE0612240084
##     https://supplier.uat1.ligentix.net/Api/Shipments/shipment/ContainerTypes/Sea
##     https://supplier.uat1.ligentix.net/Api/Shipments/shipment/Currencies/44187 (44187 is the client id)
##     https://supplier.uat1.ligentix.net/Api/Shipments/shipment/PackTypes
##
##
############################################################################

############################################################################
##   
## When opening Booking: SE0612240084
## - App URL: 
##   https://supplier.uat1.ligentix.net/shipments/container-stuffing/Sea/FCL/SE0612240084
## - Invoke GET
##   https://supplier.uat1.ligentix.net/Api/Shipments/bookingSearch/SE0612240084
##   https://supplier.uat1.ligentix.net/Api/Shipments/shipment/Details/SE0612240084
##   https://supplier.uat1.ligentix.net/Api/Shipments/shipment/SummaryInformation/SE0612240084
##   https://supplier.uat1.ligentix.net/Api/Shipments/shipment/ContainerTypes/Sea
##   https://supplier.uat1.ligentix.net/Api/Shipments/shipment/Currencies/44187
##   https://supplier.uat1.ligentix.net/Api/Shipments/shipment/PackTypes
##
## 
##
##
##
##


export BASE_URL_PROD_=https://supplier.ligentix.net
export BASE_URL=$BASE_URL_PROD_
export BASE_URL_UAT_=https://supplier.uat1.ligentix.net
export BASE_URL=$BASE_URL_UAT_

JWT_TOKEN=$(cat data/browser/jwt.txt)
export JWT_TOKEN

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"
}

logE() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >&2
}

logW() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >&2
}

allSuppliers() {
    local shipmentNum="$1"
    local resTmpFile

    resTmpFile=$(mktemp) || return 1
    
    URL="${BASE_URL%/}/Api/Shipments/bookingSearch/suppliers"
    logW "invoking $URL ..."
    HTTP_STATUS=$(
        curl -sS --get \
            "$URL" \
            -H "Authorization: Bearer $JWT_TOKEN" \
            -H "Accept: application/json" \
            --output "$resTmpFile" \
            --write-out "%{http_code}"
    )
    local curl_exit_code=$?

    if (( curl_exit_code == 0 )); then
      if [[ $HTTP_STATUS == "200" ]]; then
        logW "http status OK: 200"
        cat "$resTmpFile"
        rm -f "$resTmpFile"
        return 0
      fi
    fi

    rm -f "$resTmpFile"
    logE "curl failed: exitCode=$curl_exit_code, httpStatus=$HTTP_STATUS"
    return $curl_exit_code
}

allCustomers() {
    local shipmentNum="$1"
    local resTmpFile

    resTmpFile=$(mktemp) || return 1
    
    URL="${BASE_URL%/}/Api/Shipments/bookingSearch/customers"
    logW "invoking $URL ..."
    HTTP_STATUS=$(
        curl -sS --get \
            "$URL" \
            -H "Authorization: Bearer $JWT_TOKEN" \
            -H "Accept: application/json" \
            --output "$resTmpFile" \
            --write-out "%{http_code}"
    )
    local curl_exit_code=$?

    if (( curl_exit_code == 0 )); then
      if [[ $HTTP_STATUS == "200" ]]; then
        logW "http status OK: 200"
        cat "$resTmpFile"
        rm -f "$resTmpFile"
        return 0
      fi
    fi

    rm -f "$resTmpFile"
    logE "curl failed: exitCode=$curl_exit_code, httpStatus=$HTTP_STATUS"
    return $curl_exit_code
}

allDeliveryModes() {
    local shipmentNum="$1"
    local resTmpFile

    resTmpFile=$(mktemp) || return 1
    
    URL="${BASE_URL%/}/Api/Shipments/bookingSearch/deliveryModes"
    logW "invoking $URL ..."
    HTTP_STATUS=$(
        curl -sS --get \
            "$URL" \
            -H "Authorization: Bearer $JWT_TOKEN" \
            -H "Accept: application/json" \
            --output "$resTmpFile" \
            --write-out "%{http_code}"
    )
    local curl_exit_code=$?

    if (( curl_exit_code == 0 )); then
      if [[ $HTTP_STATUS == "200" ]]; then
        logW "http status OK: 200"
        cat "$resTmpFile"
        rm -f "$resTmpFile"
        return 0
      fi
    fi

    rm -f "$resTmpFile"
    logE "curl failed: exitCode=$curl_exit_code, httpStatus=$HTTP_STATUS"
    return $curl_exit_code
}

allPOLs() {
    local shipmentNum="$1"
    local resTmpFile

    resTmpFile=$(mktemp) || return 1
    
    URL="${BASE_URL%/}/Api/Shipments/bookingSearch/pols"
    logW "invoking $URL ..."
    HTTP_STATUS=$(
        curl -sS --get \
            "$URL" \
            -H "Authorization: Bearer $JWT_TOKEN" \
            -H "Accept: application/json" \
            --output "$resTmpFile" \
            --write-out "%{http_code}"
    )
    local curl_exit_code=$?

    if (( curl_exit_code == 0 )); then
      if [[ $HTTP_STATUS == "200" ]]; then
        logW "http status OK: 200"
        cat "$resTmpFile"
        rm -f "$resTmpFile"
        return 0
      fi
    fi

    rm -f "$resTmpFile"
    logE "curl failed: exitCode=$curl_exit_code, httpStatus=$HTTP_STATUS"
    return $curl_exit_code
}

allContainerTypes() {
    local shipmentNum="$1"
    local resTmpFile

    resTmpFile=$(mktemp) || return 1
    
    URL="${BASE_URL%/}/Api/Shipments/shipment/ContainerTypes/Sea"
    logW "invoking $URL ..."
    HTTP_STATUS=$(
        curl -sS --get \
            "$URL" \
            -H "Authorization: Bearer $JWT_TOKEN" \
            -H "Accept: application/json" \
            --output "$resTmpFile" \
            --write-out "%{http_code}"
    )
    local curl_exit_code=$?

    if (( curl_exit_code == 0 )); then
      if [[ $HTTP_STATUS == "200" ]]; then
        logW "http status OK: 200"
        cat "$resTmpFile"
        rm -f "$resTmpFile"
        return 0
      fi
    fi

    rm -f "$resTmpFile"
    logE "curl failed: exitCode=$curl_exit_code, httpStatus=$HTTP_STATUS"
    return $curl_exit_code
}

allVesselNames() {
    local shipmentNum="$1"
    local resTmpFile

    resTmpFile=$(mktemp) || return 1
    
    URL="${BASE_URL%/}/Api/Shipments/bookingSearch/vesselNames"
    logW "invoking $URL ..."
    HTTP_STATUS=$(
        curl -sS --get \
            "$URL" \
            -H "Authorization: Bearer $JWT_TOKEN" \
            -H "Accept: application/json" \
            --output "$resTmpFile" \
            --write-out "%{http_code}"
    )
    local curl_exit_code=$?

    if (( curl_exit_code == 0 )); then
      if [[ $HTTP_STATUS == "200" ]]; then
        logW "http status OK: 200"
        cat "$resTmpFile"
        rm -f "$resTmpFile"
        return 0
      fi
    fi

    rm -f "$resTmpFile"
    logE "curl failed: exitCode=$curl_exit_code, httpStatus=$HTTP_STATUS"
    return $curl_exit_code
}


allPackageTypes() {
    local shipmentNum="$1"
    local resTmpFile

    resTmpFile=$(mktemp) || return 1
    
    URL="${BASE_URL%/}/Api/Shipments/shipment/PackTypes"
    logW "invoking $URL ..."
    HTTP_STATUS=$(
        curl -sS --get \
            "$URL" \
            -H "Authorization: Bearer $JWT_TOKEN" \
            -H "Accept: application/json" \
            --output "$resTmpFile" \
            --write-out "%{http_code}"
    )
    local curl_exit_code=$?

    if (( curl_exit_code == 0 )); then
      if [[ $HTTP_STATUS == "200" ]]; then
        logW "http status OK: 200"
        cat "$resTmpFile"
        rm -f "$resTmpFile"
        return 0
      fi
    fi

    rm -f "$resTmpFile"
    logE "curl failed: exitCode=$curl_exit_code, httpStatus=$HTTP_STATUS"
    return $curl_exit_code
}


allCurrenciesByClientId() {
    local clientId="${1-}"
    local resTmpFile

    if [[ -z $clientId ]]; then
      logE "missing clientId"
      return 1
    fi

    resTmpFile=$(mktemp) || return 1
    
    URL="${BASE_URL%/}/Api/Shipments/shipment/Currencies/$clientId"
    logW "invoking $URL ..."
    HTTP_STATUS=$(
        curl -sS --get \
            "$URL" \
            -H "Authorization: Bearer $JWT_TOKEN" \
            -H "Accept: application/json" \
            --output "$resTmpFile" \
            --write-out "%{http_code}"
    )
    local curl_exit_code=$?

    if (( curl_exit_code == 0 )); then
      if [[ $HTTP_STATUS == "200" ]]; then
        logW "http status OK: 200"
        cat "$resTmpFile"
        rm -f "$resTmpFile"
        return 0
      fi
    fi

    rm -f "$resTmpFile"
    logE "curl failed: exitCode=$curl_exit_code, httpStatus=$HTTP_STATUS"
    return $curl_exit_code
}

shipmentSearch() {
    local shipmentNum="${1-}"
    local resTmpFile

    if [[ -z $shipmentNum ]]; then
      logE "missing shipmentNum"
      return 1
    fi

    resTmpFile=$(mktemp) || return 1
    
    URL="${BASE_URL%/}/Api/Shipments/shipmentSearch/shipment"
    logW "invoking $URL ..."
    HTTP_STATUS=$(
        curl -sS --get \
            "$URL" \
            -H "Authorization: Bearer $JWT_TOKEN" \
            -H "Accept: application/json" \
            --data-urlencode "pageNumber=1" \
            --data-urlencode "cwRefSearchTerm=$shipmentNum" \
            --output "$resTmpFile" \
            --write-out "%{http_code}"
    )
    local curl_exit_code=$?

    if (( curl_exit_code == 0 )); then
      if [[ $HTTP_STATUS == "200" ]]; then
        logW "http status OK: 200"
        cat "$resTmpFile"
        rm -f "$resTmpFile"
        return 0
      fi
    fi

    rm -f "$resTmpFile"
    logE "curl failed: exitCode=$curl_exit_code, httpStatus=$HTTP_STATUS"
    return $curl_exit_code
}


shipmentBookingSearch() {
    local bookingNum="${1-}"
    local resTmpFile

    if [[ -z $bookingNum ]]; then
      logE "missing bookingNum"
      return 1
    fi

    resTmpFile=$(mktemp) || return 1
    
    URL="${BASE_URL%/}/Api/Shipments/bookingSearch/$bookingNum"
    logW "invoking $URL ..."
    HTTP_STATUS=$(
        curl -sS --get \
            "$URL" \
            -H "Authorization: Bearer $JWT_TOKEN" \
            -H "Accept: application/json" \
            --data-urlencode "pageNumber=1" \
            --data-urlencode "cwRefSearchTerm=$shipmentNum" \
            --output "$resTmpFile" \
            --write-out "%{http_code}"
    )
    local curl_exit_code=$?

    if (( curl_exit_code == 0 )); then
      if [[ $HTTP_STATUS == "200" ]]; then
        logW "http status OK: 200"
        cat "$resTmpFile"
        rm -f "$resTmpFile"
        return 0
      fi
    fi

    rm -f "$resTmpFile"
    logE "curl failed: exitCode=$curl_exit_code, httpStatus=$HTTP_STATUS"
    return $curl_exit_code
}

shipmentDetails() {
    local bookingNum="${1-}"
    local resTmpFile

    if [[ -z $bookingNum ]]; then
      logE "missing bookingNum"
      return 1
    fi

    resTmpFile=$(mktemp) || return 1
    
    URL="${BASE_URL%/}/Api/Shipments/shipment/Details/$bookingNum"
    logW "invoking $URL ..."
    HTTP_STATUS=$(
        curl -sS --get \
            "$URL" \
            -H "Authorization: Bearer $JWT_TOKEN" \
            -H "Accept: application/json" \
            --data-urlencode "pageNumber=1" \
            --data-urlencode "cwRefSearchTerm=$shipmentNum" \
            --output "$resTmpFile" \
            --write-out "%{http_code}"
    )
    local curl_exit_code=$?

    if (( curl_exit_code == 0 )); then
      if [[ $HTTP_STATUS == "200" ]]; then
        logW "http status OK: 200"
        cat "$resTmpFile"
        rm -f "$resTmpFile"
        return 0
      fi
    fi

    rm -f "$resTmpFile"
    logE "curl failed: exitCode=$curl_exit_code, httpStatus=$HTTP_STATUS"
    return $curl_exit_code
}


shipmentSummary() {
    local bookingNum="${1-}"
    local resTmpFile

    if [[ -z $bookingNum ]]; then
      logE "missing bookingNum"
      return 1
    fi

    resTmpFile=$(mktemp) || return 1
    
    URL="${BASE_URL%/}/Api/Shipments/shipment/SummaryInformation/$bookingNum"
    logW "invoking $URL ..."
    HTTP_STATUS=$(
        curl -sS --get \
            "$URL" \
            -H "Authorization: Bearer $JWT_TOKEN" \
            -H "Accept: application/json" \
            --data-urlencode "pageNumber=1" \
            --data-urlencode "cwRefSearchTerm=$shipmentNum" \
            --output "$resTmpFile" \
            --write-out "%{http_code}"
    )
    local curl_exit_code=$?

    if (( curl_exit_code == 0 )); then
      if [[ $HTTP_STATUS == "200" ]]; then
        logW "http status OK: 200"
        cat "$resTmpFile"
        rm -f "$resTmpFile"
        return 0
      fi
    fi

    rm -f "$resTmpFile"
    logE "curl failed: exitCode=$curl_exit_code, httpStatus=$HTTP_STATUS"
    return $curl_exit_code
}

## #################################################################################
## ## First, search booking number from shipment number
## #################################################################################
##
## ## Scenario 1
## shipmentNum=S01863302       ## bookingNum=SE0612240084 
## shipmentNum=S01889327       ## bookingNum=SE1212240411
##
## if jsonStr=$(shipmentSearch $shipmentNum); then
##   echo "$jsonStr" | jq .
## fi
## echo "$jsonStr" | jq . > "data/Data Extraction/Scenario 1/$shipmentNum/api/shipmentSearch.res.json"
## 
## ## currencies
## if clientId="$(jq -er '.results[0].consignee.id // empty' <<< "$jsonStr")" && [[ -n "$clientId" ]] && 
##    bookingNum="$(jq -er '.results[0].bookingNumber // empty' <<< "$jsonStr")" && [[ -n "$bookingNum" ]]; then
##  if jsonStr=$(allCurrenciesByClientId "$clientId"); then
##    echo "$jsonStr" | jq .
##  fi
## fi
## echo "$jsonStr" | jq . > "data/Data Extraction/Scenario 1/$shipmentNum/api/currencies.res.json"
##
## ## shipment booking search
## if [[ -n "bookingNum" ]]; then
##   if jsonStr=$(shipmentBookingSearch $bookingNum); then 
##     echo "$jsonStr" | jq .
##   fi
## fi
## echo "$jsonStr" | jq . > "data/Data Extraction/Scenario 1/$shipmentNum/api/shipmentBookingSearch.res.json"
##
## ## shipment summary
## if [[ -n "bookingNum" ]]; then
##   if jsonStr=$(shipmentSummary $bookingNum); then 
##     echo "$jsonStr" | jq .
##   fi
## fi
## echo "$jsonStr" | jq . > "data/Data Extraction/Scenario 1/$shipmentNum/api/shipmentSummary.res.json"
##
## ## shipment details
## if [[ -n "bookingNum" ]]; then
##   if jsonStr=$(shipmentDetails $bookingNum); then 
##     echo "$jsonStr" | jq .
##   fi
## fi
## echo "$jsonStr" | jq . > "data/Data Extraction/Scenario 1/$shipmentNum/api/shipmentDetails.res.json"
##
##
