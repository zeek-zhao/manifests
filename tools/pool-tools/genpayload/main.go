// genpayload — 生成 imgcrypt ctd-decoder 所需的 fd3 payload（io.containerd.ocicrypt.v1.Payload）。
//
// 背景（DSN-20261128-017）：containerd 自动解密管线在 pull 时构造的 payload TypeUrl 为空
// （F-19），消费侧解密必须走 ctd-decoder 手动路径：密文层走 stdin，payload 走 fd3。
// 本工具在 CI 加密完成后运行（此时加密 blob 的 digest/annotations 已定），
// 产物 payload.bin 随 -meta 镜像分发，消费侧无需 go 环境。
//
// 用法: genpayload --descriptor <descriptor.json> --out <payload.bin>
//   descriptor.json 为加密后镜像 manifest 中对应 layer 的 JSON（含 digest/annotations）。
//
// 依赖 imgcrypt 模块上下文：go run 本文件时 CWD 必须位于 imgcrypt 源码树内
// （pool_build 经 GENPAYLOAD_DIR 指定树内独立子目录，避免与树根包名冲突）。
// Marshal 必须用 containerd 的 proto shim（gogo 兼容），不能用 google.golang.org/protobuf。
package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"os"

	"github.com/containerd/containerd/v2/pkg/protobuf/proto"
	"github.com/containerd/containerd/v2/pkg/protobuf/types"
	"github.com/containerd/imgcrypt/v2"
	"github.com/containerd/typeurl/v2"
	ocispec "github.com/opencontainers/image-spec/specs-go/v1"
)

func main() {
	descPath := flag.String("descriptor", "", "加密 layer 的 descriptor JSON 路径")
	outPath := flag.String("out", "payload.bin", "payload 输出路径")
	flag.Parse()
	if *descPath == "" {
		fmt.Fprintln(os.Stderr, "--descriptor 必填")
		os.Exit(2)
	}
	data, err := os.ReadFile(*descPath)
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
	if err := os.WriteFile(*outPath, b, 0o644); err != nil {
		panic(err)
	}
	fmt.Printf("payload: %d bytes, TypeUrl=%s\n", len(b), ta.TypeUrl)
}
