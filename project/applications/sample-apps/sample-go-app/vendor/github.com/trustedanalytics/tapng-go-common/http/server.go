/**
 * Copyright (c) 2016 Intel Corporation
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *    http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package http

import (
	"fmt"
	"github.com/gocraft/web"
	"log"
	"net/http"
	"os"
)

func GetListenAddress() string {
	address := os.Getenv("BIND_ADDRESS")
	if address == "" {
		address = "0.0.0.0"
	}
	port := os.Getenv("PORT")
	if port == "" {
		port = "80"
	}
	return fmt.Sprintf("%v:%v", address, port)
}

func StartServer(r *web.Router) {
	listenOn := GetListenAddress()
	log.Println("Will listen on:", listenOn)
	err := http.ListenAndServe(listenOn, r)
	if err != nil {
		logger.Critical("Couldn't serve app on ", listenOn, " Error:", err)
	}
}

func StartServerTLS(sslCertLocation, sslKeyLocation string, r *web.Router) {
	listenOn := GetListenAddress()
	log.Println("TLS Will listen on:", listenOn)
	err := http.ListenAndServeTLS(listenOn, sslCertLocation, sslKeyLocation, r)
	if err != nil {
		logger.Critical("Couldn't serve app on ", listenOn, " Error:", err)
	}
}
