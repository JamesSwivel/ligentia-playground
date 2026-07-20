#!/usr/bin/bash

############################################################################
##
## NOTE:
## - Get booking order by shipment number
##   GET https://supplier.uat1.ligentix.net/Api/Shipments/shipmentSearch/shipment
##     ?pageNumber=1&itemsPerPage=10&cwRefSearchTerm=S01863302&orderByFieldName=etd&orderByDirection=ask\
## - Get booking order
##   GET https://supplier.uat1.ligentix.net/Api/Shipments/bookingSearch/SE0612240084
##   GET https://supplier.uat1.ligentix.net/Api/Shipments/shipment/SummaryInformation/SE0612240084
##   GET https://supplier.uat1.ligentix.net/Api/Shipments/shipment/Details/SE0612240084
## - Get suppliers
##   GET https://supplier.uat1.ligentix.net/Api/Shipments/bookingSearch/suppliers
## - Get customers
##   GET https://supplier.uat1.ligentix.net/Api/Shipments/bookingSearch/customers
## - Get delivery modes
##   GET https://supplier.uat1.ligentix.net/Api/Shipments/bookingSearch/deliveryModes
## - Get POLs
##   GET https://supplier.uat1.ligentix.net/Api/Shipments/bookingSearch/pols
## - Get container types
##   GET https://supplier.uat1.ligentix.net/Api/Shipments/shipment/ContainerTypes/Sea
## - Get vessel names
##   GET https://supplier.uat1.ligentix.net/Api/Shipments/bookingSearch/vesselNames
## - Get package types
##   GET https://supplier.uat1.ligentix.net/Api/Shipments/shipment/PackTypes
## - Get currencies
##   GET https://supplier.uat1.ligentix.net/Api/Shipments/shipment/Currencies/26317
##
############################################################################

export BASE_URL_PROD_=https://supplier.ligentix.net
export BASE_URL=$BASE_URL_PROD_
export BASE_URL_UAT_=https://supplier.uat1.ligentix.net
export BASE_URL=$BASE_URL_UAT_

JWT_TOKEN=$(cat srcTest/joe/temp/jwt.txt)
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


allCurrencies() {
    local shipmentNum="$1"
    local resTmpFile

    resTmpFile=$(mktemp) || return 1
    
    URL="${BASE_URL%/}/Api/Shipments/shipment/Currencies/26317"
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
    local shipmentNum="$1"
    local resTmpFile

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

if jsonStr=$(shipmentSearch S01942131); then
  echo "$jsonStr" | jq .
fi
