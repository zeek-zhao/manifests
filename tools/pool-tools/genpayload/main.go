//go:build ignore

package main

import (
	"encoding/json"
	"fmt"
	"os"

	"github.com/containerd/containerd/v2/pkg/protobuf/proto"
	"github.com/containerd/containerd/v2/pkg/protobuf/types"
	"github.com/containerd/imgcrypt/v2"
	"github.com/containerd/typeurl/v2"
	ocispec "github.com/opencontainers/image-spec/specs-go/v1"
)

func main() {
	data, err := os.ReadFile("/mnt/descriptor1.json")
	if err != nil {
		panic(err)
	}
	var desc ocispec.Descriptor
	if err := json.Unmarshal(data, &desc); err != nil {
		panic(err)
	}
	p := imgcrypt.Payload{Descriptor: desc}
	anyP, err := typeurl.MarshalAny(&p)
	if err != nil {
		panic(err)
	}
	ta := &types.Any{TypeUrl: anyP.GetTypeUrl(), Value: anyP.GetValue()}
	b, err := proto.Marshal(ta)
	if err != nil {
		panic(err)
	}
	if err := os.WriteFile("/mnt/payload1.bin", b, 0644); err != nil {
		panic(err)
	}
	fmt.Println("payload1.bin:", len(b), "bytes, TypeUrl:", ta.TypeUrl)
}
