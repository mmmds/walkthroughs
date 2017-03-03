<?php

//configuration
$file = "/tmp/traffic";
$host = "example.com";
$url = "https://" . $host;

//setup curl
$c = curl_init();
curl_setopt($c, CURLOPT_RETURNTRANSFER, 1);
curl_setopt($c, CURLOPT_VERBOSE, 1);
curl_setopt($c, CURLOPT_HEADER, 1);
curl_setopt($c, CURLOPT_SSL_VERIFYHOST, 0);
curl_setopt($c, CURLOPT_SSL_VERIFYPEER, 0);
$body = NULL;

//prepare request
$path = $_SERVER['REQUEST_URI'];
curl_setopt($c, CURLOPT_URL, $url . $path);

$headers = array();
foreach (getallheaders() as $name => $value) {
        if (strcasecmp($name, "Host") == 0) {
			array_push($headers, "Host: " . $host);
        } else if (strcasecmp($name, "referer") != 0 && strcasecmp($name, "Accept-Encoding") != 0) {        
			array_push($headers, $name . ": " . $value);
        }
}
curl_setopt($c, CURLOPT_HTTPHEADER, $headers);

$method = $_SERVER['REQUEST_METHOD'];
curl_setopt($c, CURLOPT_CUSTOMREQUEST, $method);

if ($method === "POST" || $method === "PUT") {
	$body = file_get_contents('php://input');
	curl_setopt($c, CURLOPT_POSTFIELDS, $body);
}

//send request
$response = curl_exec($c);

//read response
$responseHeaderSize = curl_getinfo($c, CURLINFO_HEADER_SIZE);
$responseHeader = substr($response, 0, $responseHeaderSize);
$responseBody = substr($response, $responseHeaderSize);

foreach (explode(PHP_EOL, $responseHeader) as $key => $val) {
	if (strpos($val, "Transfer-Encoding: chunked") === false) {
		header($val, true);
	}
}
echo $responseBody;

$responseCode = curl_getinfo($c, CURLINFO_HTTP_CODE);	
http_response_code($responseCode);

//log request and response
$data = $method . " " . $path . " " . $_SERVER['SERVER_PROTOCOL'] . "\n";
$data .= implode("\n", $headers);
$data .= "\n\n";
if (isset($body)) {
	$data .= $body . "\n\n";
}
$data .= "\n";
$data .= str_replace("\r", "", $response);
$data .= "\n------------\n";
file_put_contents($file, $data, FILE_APPEND | LOCK_EX);

?>
