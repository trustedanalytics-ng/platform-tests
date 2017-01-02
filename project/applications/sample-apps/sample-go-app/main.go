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

package main

import (
	"fmt"
	"github.com/gocraft/web"
	httpGoCommon "github.com/trustedanalytics/tapng-go-common/http"
	"github.com/trustedanalytics/tapng-go-common/logger"
	"net/http"
)

var (
	logger = logger_wrapper.InitLogger("main")
)

func Healthz(rw web.ResponseWriter, req *web.Request) {
	rw.WriteHeader(http.StatusOK)
	fmt.Fprintf(rw, "OK\n")
}

type ApiContext struct{}

func NewApiContext() *ApiContext {
	return &ApiContext{}
}

func main() {
	context := NewApiContext()
	router := web.New(*context)
	router.Get("/", Healthz)
	router.Get("/healthz", Healthz)
	apiRouter := router.Subrouter(*context, "/api")

	v1Router := apiRouter.Subrouter(*context, "/v1")
	v1Router.Get("/healthz", Healthz)

	v1AliasRouter := apiRouter.Subrouter(*context, "/v1.0")
	v1AliasRouter.Get("/healthz", Healthz)

	httpGoCommon.StartServer(router)
}
