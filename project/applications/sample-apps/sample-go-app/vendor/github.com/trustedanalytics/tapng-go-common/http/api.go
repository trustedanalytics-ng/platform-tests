package http

import (
	"encoding/json"
	"errors"
	"fmt"
	"net/http"
)

type ApiConnector struct {
	BasicAuth *BasicAuth
	Client    *http.Client
	Url       string
}

func GetModel(apiConnector ApiConnector, expectedStatus int, result interface{}) error {
	status, body, err := RestGET(apiConnector.Url, apiConnector.BasicAuth, apiConnector.Client)
	if err != nil {
		return err
	}

	err = json.Unmarshal(body, result)
	if err != nil {
		return err
	}

	if status != expectedStatus {
		return getWrongStatusError(status, expectedStatus, string(body))
	}
	return nil
}

func PatchModel(apiConnector ApiConnector, requestBody interface{}, expectedStatus int, result interface{}) error {
	requestBodyByte, err := json.Marshal(requestBody)
	if err != nil {
		return err
	}

	status, body, err := RestPATCH(apiConnector.Url, string(requestBodyByte), apiConnector.BasicAuth, apiConnector.Client)
	if err != nil {
		return err
	}

	err = json.Unmarshal(body, result)
	if err != nil {
		return err
	}

	if status != expectedStatus {
		return getWrongStatusError(status, expectedStatus, string(body))
	}
	return nil
}

func AddModel(apiConnector ApiConnector, requestBody interface{}, expectedStatus int, result interface{}) error {
	requestBodyByte, err := json.Marshal(requestBody)
	if err != nil {
		return err
	}

	status, body, err := RestPOST(apiConnector.Url, string(requestBodyByte), apiConnector.BasicAuth, apiConnector.Client)
	if err != nil {
		return err
	}

	err = json.Unmarshal(body, result)
	if err != nil {
		return err
	}

	if status != expectedStatus {
		return getWrongStatusError(status, expectedStatus, string(body))
	}
	return nil
}

func getWrongStatusError(status, expectedStatus int, body string) error {
	return errors.New(fmt.Sprintf("Bad response status: %d, expected status was: % d. Resposne body: %s", status, expectedStatus, body))
}
