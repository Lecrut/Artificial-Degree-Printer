from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from adk.agents.base import BaseAgent
from adk.core.events import EventType
from adk.core.models import ChapterDraft, CodeArtifact
from adk.core.state import ADKProjectState


@dataclass
class LanguageProfile:
    """Represents a discovered and synthesized ecosystem profile for any programming language."""
    language: str
    extension: str
    build_file_name: str
    build_file_content: str
    service_file_name: str
    service_code: str
    entrypoint_file_name: str
    entrypoint_code: str
    test_framework: str
    test_file_name: str
    test_code: str
    docker_base_image: str
    dockerfile_content: str
    recommended_framework: str
    paradigm: str = "Object-Oriented & Structural"
    build_file_language: str = ""
    doc_urls: List[str] = field(default_factory=list)


class DynamicLanguageResolver:
    """
    Autonomous Language and Framework Discovery Engine:
    Inspects user requests, discovers technology stacks, queries documentation,
    and produces a tailored LanguageProfile for any programming language.
    """

    @classmethod
    def resolve_profile(cls, state: ADKProjectState, doc_scraper: Optional[Any] = None) -> LanguageProfile:
        text_corpus = f"{state.request} {state.metadata.title} ".lower()
        for req in state.requirements:
            text_corpus += f" {req.title} {req.description}".lower()

        # 1. Zig
        if re.search(r"\bzig\b|w zig\b|in zig\b", text_corpus):
            return cls._profile_zig()

        # 2. Elixir
        if re.search(r"\belixir\b|\bphoenix\b|w elixirze\b|in elixir\b", text_corpus):
            return cls._profile_elixir()

        # 3. Haskell
        if re.search(r"\bhaskell\b|\bcabal\b|\bstack\b|w haskellu\b|in haskell\b", text_corpus):
            return cls._profile_haskell()

        # 4. Scala
        if re.search(r"\bscala\b|\bsbt\b|\bakka\b|\bzio\b|w scala\b|in scala\b", text_corpus):
            return cls._profile_scala()

        # 5. Julia
        if re.search(r"\bjulia\b|w julii\b|in julia\b", text_corpus):
            return cls._profile_julia()

        # 6. Go (Golang)
        if re.search(r"\b(golang|go)\b|w go\b|in go\b|\bgin\b|\bgoroutine\b", text_corpus):
            return cls._profile_go()

        # 7. Rust
        if re.search(r"\b(rust|cargo|actix|tokio|axum|wasm)\b|w rust\b|in rust\b", text_corpus):
            return cls._profile_rust()

        # 8. TypeScript / Node.js
        if re.search(r"\b(typescript|ts|node|nodejs|nest|express|nextjs|react)\b|w typescript\b|in typescript\b", text_corpus):
            return cls._profile_typescript()

        # 9. Flutter / Dart
        if re.search(r"\b(flutter|dart)\b|mobile app|aplikacja mobilna|\bandroid\b|\bios\b|w flutterze|we flutter", text_corpus):
            return cls._profile_flutter()

        # 10. C++
        if re.search(r"c\+\+|\bcpp\b|\bcmake\b|\bqt\b", text_corpus):
            return cls._profile_cpp()

        # 11. C# / .NET
        if re.search(r"c#|\bcsharp\b|\bdotnet\b|\.net|asp\.net", text_corpus):
            return cls._profile_csharp()

        # 12. Kotlin / Java
        if re.search(r"\bkotlin\b|\bjava\b|\bspring\b|\bktor\b|w kotlinie|in kotlin", text_corpus):
            return cls._profile_kotlin()

        # 13. Swift
        if re.search(r"\bswift\b|\bswiftui\b|\bvapor\b|w swift|in swift", text_corpus):
            return cls._profile_swift()

        # 14. Python
        if re.search(r"\b(python|py|fastapi|django|flask|pytorch)\b|w pythonie|w python\b|in python\b", text_corpus):
            return cls._profile_python()

        # 15. Dynamic Generic Fallback for Any Arbitrary Requested Language
        detected_lang_match = re.search(
            r"\b(?:w\s+języku|w\s+technologii|w\s+ekosystemie|in\s+language|in\s+the\s+language\s+of|written\s+in)\s+([a-zA-Z\+\#]{2,15})",
            text_corpus
        )
        if detected_lang_match:
            custom_lang = detected_lang_match.group(1).capitalize()
            return cls._profile_generic(custom_lang, doc_scraper)

        # Default Python
        return cls._profile_python()

    # -------------------------------------------------------------------------
    # Profile Definitions
    # -------------------------------------------------------------------------
    @classmethod
    def _profile_zig(cls) -> LanguageProfile:
        build_zig = """const std = @import("std");

pub fn build(b: *std.Build) void {
    const target = b.standardTargetOptions(.{});
    const optimize = b.standardOptimizeOption(.{});

    const lib = b.addStaticLibrary(.{
        .name = "core_service",
        .root_source_file = b.path("src/service.zig"),
        .target = target,
        .optimize = optimize,
    });
    b.installArtifact(lib);

    const main_tests = b.addTest(.{
        .root_source_file = b.path("tests/service_test.zig"),
        .target = target,
        .optimize = optimize,
    });
    const run_main_tests = b.addRunArtifact(main_tests);
    const test_step = b.step("test", "Run library tests");
    test_step.dependOn(&run_main_tests.step);
}
"""
        service_zig = """const std = @import("std");

pub const ProcessingTask = struct {
    task_id: []const u8,
    status: []const u8,
};

pub const CoreProcessingService = struct {
    service_name: []const u8,
    allocator: std.mem.Allocator,

    pub fn init(allocator: std.mem.Allocator, service_name: []const u8) CoreProcessingService {
        return .{
            .service_name = service_name,
            .allocator = allocator,
        };
    }

    pub fn submitTask(self: *CoreProcessingService, task_id: []const u8) ProcessingTask {
        _ = self;
        return .{
            .task_id = task_id,
            .status = "pending",
        };
    }

    pub fn executeTask(self: *CoreProcessingService, task_id: []const u8) ![]const u8 {
        _ = self;
        _ = task_id;
        return "completed";
    }
};
"""
        main_zig = """const std = @import("std");
const service = @import("service.zig");

pub fn main() !void {
    var gpa = std.heap.GeneralPurposeAllocator(.{}){};
    defer _ = gpa.deinit();
    const allocator = gpa.allocator();

    var s = service.CoreProcessingService.init(allocator, "ZigEngineService");
    std.debug.print("Started Zig Service: {s}\\n", .{s.service_name});
}
"""
        test_zig = """const std = @import("std");
const service = @import("../src/service.zig");

test "CoreProcessingService initialization and execution" {
    var s = service.CoreProcessingService.init(std.testing.allocator, "TestZigService");
    try std.testing.expectEqualStrings("TestZigService", s.service_name);

    const task = s.submitTask("T-1");
    try std.testing.expectEqualStrings("pending", task.status);

    const res = try s.executeTask("T-1");
    try std.testing.expectEqualStrings("completed", res);
}
"""
        dockerfile = """FROM ziglang/zig:latest AS builder
WORKDIR /app
COPY build.zig ./
COPY src/ src/
COPY tests/ tests/
RUN zig build -Doptimize=ReleaseFast

FROM alpine:latest
WORKDIR /root/
CMD ["zig", "version"]
"""
        return LanguageProfile(
            language="Zig",
            extension=".zig",
            build_file_name="build.zig",
            build_file_content=build_zig,
            service_file_name="src/service.zig",
            service_code=service_zig,
            entrypoint_file_name="src/main.zig",
            entrypoint_code=main_zig,
            test_framework="zig test",
            test_file_name="tests/service_test.zig",
            test_code=test_zig,
            docker_base_image="ziglang/zig:latest",
            dockerfile_content=dockerfile,
            recommended_framework="Zig Standard Library / Zap",
            paradigm="Systems Programming & Explicit Memory",
            doc_urls=["https://ziglang.org/documentation/master/"],
        )

    @classmethod
    def _profile_elixir(cls) -> LanguageProfile:
        mix_exs = """defmodule CoreService.MixProject do
  use Mix.Project

  def project do
    [
      app: :core_service,
      version: "0.1.0",
      elixir: "~> 1.15",
      start_permanent: Mix.env() == :prod,
      deps: deps()
    ]
  end

  def application do
    [extra_applications: [:logger]]
  end

  defp deps do
    [{:jason, "~> 1.4"}]
  end
end
"""
        service_ex = """defmodule CoreService do
  @moduledoc \"\"\"
  Core processing engine implemented in Elixir / OTP.
  \"\"\"

  defstruct service_name: "ElixirEngineService", tasks: %{}

  def new(service_name \\\\ "ElixirEngineService") do
    %CoreService{service_name: service_name}
  end

  def submit_task(%CoreService{} = state, task_id, payload) do
    task = %{task_id: task_id, payload: payload, status: :pending}
    {:ok, task, %{state | tasks: Map.put(state.tasks, task_id, task)}}
  end

  def execute_task(%CoreService{} = state, task_id) do
    case Map.get(state.tasks, task_id) do
      nil -> {:error, :not_found}
      task -> {:ok, %{task | status: :completed}}
    end
  end
end
"""
        test_ex = """defmodule CoreServiceTest do
  use ExUnit.Case
  doctest CoreService

  test "initializes and processes tasks" do
    service = CoreService.new("TestElixirService")
    assert service.service_name == "TestElixirService"

    {:ok, task, updated_service} = CoreService.submit_task(service, "T-1", %{count: 3})
    assert task.status == :pending

    {:ok, completed_task} = CoreService.execute_task(updated_service, "T-1")
    assert completed_task.status == :completed
  end
end
"""
        dockerfile = """FROM elixir:1.15-alpine
WORKDIR /app
COPY mix.exs ./
RUN mix local.hex --force && mix local.rebar --force
COPY lib/ lib/
COPY test/ test/
RUN mix test
CMD ["iex", "-S", "mix"]
"""
        return LanguageProfile(
            language="Elixir",
            extension=".ex",
            build_file_name="mix.exs",
            build_file_content=mix_exs,
            service_file_name="lib/core_service.ex",
            service_code=service_ex,
            entrypoint_file_name="lib/core_service.ex",
            entrypoint_code=service_ex,
            test_framework="ExUnit (mix test)",
            test_file_name="test/core_service_test.exs",
            test_code=test_ex,
            docker_base_image="elixir:1.15-alpine",
            dockerfile_content=dockerfile,
            recommended_framework="Phoenix / OTP GenServer",
            paradigm="Functional & Actor Model (BEAM)",
            doc_urls=["https://hexdocs.pm/elixir/"],
        )

    @classmethod
    def _profile_haskell(cls) -> LanguageProfile:
        stack_yaml = """resolver: lts-21.0
packages:
- .
extra-deps: []
"""
        service_hs = """module CoreService
    ( CoreProcessingService(..)
    , ProcessingTask(..)
    , initService
    , executeTask
    ) where

data ProcessingTask = ProcessingTask
    { taskId :: String
    , status :: String
    } deriving (Show, Eq)

data CoreProcessingService = CoreProcessingService
    { serviceName :: String
    } deriving (Show, Eq)

initService :: String -> CoreProcessingService
initService name = CoreProcessingService name

executeTask :: String -> ProcessingTask
executeTask tId = ProcessingTask tId "completed"
"""
        test_hs = """module Main where

import CoreService
import Test.Hspec

main :: IO ()
main = hspec $ do
  describe "CoreService" $ do
    it "initializes correctly and completes task" $ do
      let service = initService "TestHaskellService"
      serviceName service `shouldBe` "TestHaskellService"
      let task = executeTask "T-1"
      status task `shouldBe` "completed"
"""
        dockerfile = """FROM haskell:9.4
WORKDIR /app
COPY stack.yaml ./
COPY src/ src/
COPY test/ test/
CMD ["stack", "test"]
"""
        return LanguageProfile(
            language="Haskell",
            extension=".hs",
            build_file_name="stack.yaml",
            build_file_content=stack_yaml,
            service_file_name="src/CoreService.hs",
            service_code=service_hs,
            entrypoint_file_name="src/Main.hs",
            entrypoint_code="module Main where\nimport CoreService\nmain = putStrLn \"Started Haskell Service\"",
            test_framework="Hspec (stack test)",
            test_file_name="test/Spec.hs",
            test_code=test_hs,
            docker_base_image="haskell:9.4",
            dockerfile_content=dockerfile,
            recommended_framework="Servant / Yesod",
            paradigm="Purely Functional & Strong Static Types",
            doc_urls=["https://www.haskell.org/documentation/"],
        )

    @classmethod
    def _profile_scala(cls) -> LanguageProfile:
        build_sbt = """name := "core-service"
version := "0.1.0"
scalaVersion := "3.3.1"

libraryDependencies ++= Seq(
  "org.scalatest" %% "scalatest" % "3.2.17" % Test
)
"""
        service_scala = """package coreservice

case class ProcessingTask(taskId: String, status: String = "pending")

class CoreProcessingService(val serviceName: String = "ScalaEngineService"):
  def submitTask(taskId: String): ProcessingTask =
    ProcessingTask(taskId, "pending")

  def executeTask(taskId: String): ProcessingTask =
    ProcessingTask(taskId, "completed")
"""
        test_scala = """package coreservice

import org.scalatest.funsuite.AnyFunSuite

class CoreProcessingServiceTest extends AnyFunSuite:
  test("initialization and execution") {
    val service = CoreProcessingService("TestScalaService")
    assert(service.serviceName == "TestScalaService")
    val task = service.executeTask("T-1")
    assert(task.status == "completed")
  }
"""
        dockerfile = """FROM hseeberger/scala-sbt:17.0.2_1.6.2_3.1.1
WORKDIR /app
COPY build.sbt ./
COPY src/ src/
RUN sbt test
CMD ["sbt", "run"]
"""
        return LanguageProfile(
            language="Scala",
            extension=".scala",
            build_file_name="build.sbt",
            build_file_content=build_sbt,
            service_file_name="src/main/scala/CoreService.scala",
            service_code=service_scala,
            entrypoint_file_name="src/main/scala/Main.scala",
            entrypoint_code="package coreservice\n@main def run() = println(\"Started Scala Service\")",
            test_framework="ScalaTest (sbt test)",
            test_file_name="src/test/scala/CoreServiceTest.scala",
            test_code=test_scala,
            docker_base_image="hseeberger/scala-sbt",
            dockerfile_content=dockerfile,
            recommended_framework="Akka / ZIO / Play Framework",
            paradigm="Functional & Object-Oriented Hybrid",
            doc_urls=["https://docs.scala-lang.org/"],
        )

    @classmethod
    def _profile_julia(cls) -> LanguageProfile:
        project_toml = """name = "CoreService"
uuid = "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d"
version = "0.1.0"

[deps]
Test = "8dfed614-e22c-5e08-85e1-65c5234f0b40"
"""
        service_jl = """module CoreService

export ProcessingTask, CoreProcessingEngine, execute_task

struct ProcessingTask
    task_id::String
    status::String
end

struct CoreProcessingEngine
    service_name::String
end

function execute_task(engine::CoreProcessingEngine, task_id::String)
    return ProcessingTask(task_id, "completed")
end

end
"""
        test_jl = """using Test
include("../src/CoreService.jl")
using .CoreService

@testset "CoreService Tests" begin
    engine = CoreProcessingEngine("JuliaEngineService")
    @test engine.service_name == "JuliaEngineService"
    task = execute_task(engine, "T-1")
    @test task.status == "completed"
end
"""
        dockerfile = """FROM julia:1.9
WORKDIR /app
COPY Project.toml ./
COPY src/ src/
COPY test/ test/
CMD ["julia", "-e", "using Pkg; Pkg.test()"]
"""
        return LanguageProfile(
            language="Julia",
            extension=".jl",
            build_file_name="Project.toml",
            build_file_content=project_toml,
            service_file_name="src/CoreService.jl",
            service_code=service_jl,
            entrypoint_file_name="src/main.jl",
            entrypoint_code="include(\"CoreService.jl\")\nprintln(\"Started Julia Service\")",
            test_framework="Test (@testset)",
            test_file_name="test/runtests.jl",
            test_code=test_jl,
            docker_base_image="julia:1.9",
            dockerfile_content=dockerfile,
            recommended_framework="Genie.jl / Flux.jl",
            paradigm="Multiple Dispatch & High-Performance Technical Computing",
            doc_urls=["https://docs.julialang.org/"],
        )

    @classmethod
    def _profile_go(cls) -> LanguageProfile:
        go_mod = "module example.com/service\n\ngo 1.22\n"
        service_go = """package main

import (
	"errors"
	"fmt"
	"sync"
)

type ProcessingTask struct {
	TaskID  string                 `json:"task_id"`
	Payload map[string]interface{} `json:"payload"`
	Status  string                 `json:"status"`
}

type CoreProcessingService struct {
	ServiceName string
	tasks       map[string]*ProcessingTask
	mu          sync.RWMutex
}

func NewCoreProcessingService(serviceName string) *CoreProcessingService {
	return &CoreProcessingService{
		ServiceName: serviceName,
		tasks:       make(map[string]*ProcessingTask),
	}
}

func (s *CoreProcessingService) SubmitTask(taskID string, payload map[string]interface{}) (*ProcessingTask, error) {
	s.mu.Lock()
	defer s.mu.Unlock()

	if _, exists := s.tasks[taskID]; exists {
		return nil, fmt.Errorf("task with ID %s already exists", taskID)
	}

	task := &ProcessingTask{TaskID: taskID, Payload: payload, Status: "pending"}
	s.tasks[taskID] = task
	return task, nil
}

func (s *CoreProcessingService) ExecuteTask(taskID string) (map[string]interface{}, error) {
	s.mu.Lock()
	defer s.mu.Unlock()

	task, exists := s.tasks[taskID]
	if !exists {
		return nil, errors.New("task not found")
	}

	task.Status = "completed"
	return map[string]interface{}{"status": "completed", "score": 1.0}, nil
}
"""
        test_go = """package main

import "testing"

func TestServiceInitialization(t *testing.T) {
	service := NewCoreProcessingService("TestGoService")
	if service.ServiceName != "TestGoService" {
		t.Fatalf("Expected TestGoService, got %s", service.ServiceName)
	}
}

func TestSubmitAndExecuteTask(t *testing.T) {
	service := NewCoreProcessingService("TestGoService")
	task, err := service.SubmitTask("T-1", map[string]interface{}{"count": 1})
	if err != nil || task.Status != "pending" {
		t.Fatalf("Submit failed")
	}
	res, err := service.ExecuteTask("T-1")
	if err != nil || res["status"] != "completed" {
		t.Fatalf("Execute failed")
	}
}
"""
        dockerfile = """FROM golang:1.22-alpine AS builder
WORKDIR /app
COPY go.mod ./
COPY src/ src/
RUN go build -o /app/server ./src

FROM alpine:latest
WORKDIR /root/
COPY --from=builder /app/server .
CMD ["./server"]
"""
        return LanguageProfile(
            language="Go",
            extension=".go",
            build_file_name="go.mod",
            build_file_content=go_mod,
            service_file_name="src/service.go",
            service_code=service_go,
            entrypoint_file_name="src/main.go",
            entrypoint_code="package main\nimport \"fmt\"\nfunc main() { fmt.Println(\"Started Go Service\") }",
            test_framework="go test",
            test_file_name="tests/service_test.go",
            test_code=test_go,
            docker_base_image="golang:1.22-alpine",
            dockerfile_content=dockerfile,
            recommended_framework="Gin / Fiber / Standard Library",
            paradigm="Concurrent & Structural Typing",
            doc_urls=["https://go.dev/doc/"],
        )

    @classmethod
    def _profile_rust(cls) -> LanguageProfile:
        cargo_toml = """[package]
name = "core_service"
version = "0.1.0"
edition = "2021"

[dependencies]
serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0"
"""
        lib_rs = """use std::collections::HashMap;

#[derive(Debug, Clone)]
pub struct ProcessingTask {
    pub task_id: String,
    pub status: String,
}

pub struct CoreProcessingService {
    pub service_name: String,
    tasks: HashMap<String, ProcessingTask>,
}

impl CoreProcessingService {
    pub fn new(service_name: &str) -> Self {
        Self {
            service_name: service_name.to_string(),
            tasks: HashMap::new(),
        }
    }

    pub fn submit_task(&mut self, task_id: &str) -> Result<ProcessingTask, String> {
        if self.tasks.contains_key(task_id) {
            return Err(format!("Task {} exists", task_id));
        }
        let task = ProcessingTask { task_id: task_id.to_string(), status: "pending".to_string() };
        self.tasks.insert(task_id.to_string(), task.clone());
        Ok(task)
    }

    pub fn execute_task(&mut self, task_id: &str) -> Result<String, String> {
        if let Some(task) = self.tasks.get_mut(task_id) {
            task.status = "completed".to_string();
            Ok("completed".to_string())
        } else {
            Err("Task not found".to_string())
        }
    }
}
"""
        test_rs = """use core_service::CoreProcessingService;

#[test]
fn test_service_initialization_and_execution() {
    let mut service = CoreProcessingService::new("TestRustService");
    assert_eq!(service.service_name, "TestRustService");
    let task = service.submit_task("T-1").expect("Submit error");
    assert_eq!(task.status, "pending");
    let status = service.execute_task("T-1").expect("Execution error");
    assert_eq!(status, "completed");
}
"""
        dockerfile = """FROM rust:1.78-slim AS builder
WORKDIR /app
COPY Cargo.toml ./
COPY src/ src/
RUN cargo build --release

FROM debian:bookworm-slim
WORKDIR /root/
COPY --from=builder /app/target/release/core_service .
CMD ["./core_service"]
"""
        return LanguageProfile(
            language="Rust",
            extension=".rs",
            build_file_name="Cargo.toml",
            build_file_content=cargo_toml,
            service_file_name="src/lib.rs",
            service_code=lib_rs,
            entrypoint_file_name="src/main.rs",
            entrypoint_code="use core_service::CoreProcessingService;\nfn main() { println!(\"Started Rust Service\"); }",
            test_framework="cargo test",
            test_file_name="tests/integration_test.rs",
            test_code=test_rs,
            docker_base_image="rust:1.78-slim",
            dockerfile_content=dockerfile,
            recommended_framework="Actix-web / Axum / Tokio",
            paradigm="Zero-Cost Abstractions & Memory Safety",
            doc_urls=["https://doc.rust-lang.org/"],
        )

    @classmethod
    def _profile_typescript(cls) -> LanguageProfile:
        pkg_json = """{
  "name": "core-service",
  "version": "1.0.0",
  "scripts": { "build": "tsc", "test": "jest" },
  "devDependencies": { "typescript": "^5.0.0", "jest": "^29.0.0", "ts-jest": "^29.0.0" }
}
"""
        service_ts = """export interface ProcessingTask {
  taskId: string;
  status: 'pending' | 'completed';
}

export class CoreProcessingService {
  public serviceName: string;
  private tasks: Map<string, ProcessingTask> = new Map();

  constructor(serviceName: string = 'TSEngineService') {
    this.serviceName = serviceName;
  }

  public submitTask(taskId: string): ProcessingTask {
    if (this.tasks.has(taskId)) throw new Error(`Task ${taskId} exists`);
    const task: ProcessingTask = { taskId, status: 'pending' };
    this.tasks.set(taskId, task);
    return task;
  }

  public executeTask(taskId: string): { status: string } {
    const task = this.tasks.get(taskId);
    if (!task) throw new Error(`Task ${taskId} not found`);
    task.status = 'completed';
    return { status: 'completed' };
  }
}
"""
        test_ts = """import { CoreProcessingService } from '../src/service';

describe('CoreProcessingService', () => {
  it('initializes and executes task', () => {
    const service = new CoreProcessingService('TestService');
    expect(service.serviceName).toBe('TestService');
    const task = service.submitTask('T-1');
    expect(task.status).toBe('pending');
    expect(service.executeTask('T-1').status).toBe('completed');
  });
});
"""
        dockerfile = """FROM node:20-alpine
WORKDIR /app
COPY package.json ./
RUN npm install
COPY src/ src/
CMD ["node", "dist/index.js"]
"""
        return LanguageProfile(
            language="TypeScript",
            extension=".ts",
            build_file_name="package.json",
            build_file_content=pkg_json,
            service_file_name="src/service.ts",
            service_code=service_ts,
            entrypoint_file_name="src/index.ts",
            entrypoint_code="import { CoreProcessingService } from './service';\nconsole.log('Started TS Service');",
            test_framework="Jest (npm test)",
            test_file_name="tests/service.test.ts",
            test_code=test_ts,
            docker_base_image="node:20-alpine",
            dockerfile_content=dockerfile,
            recommended_framework="NestJS / Express / Fastify",
            paradigm="Typed JavaScript & Asynchronous Event-Driven",
            doc_urls=["https://www.typescriptlang.org/docs/"],
        )

    @classmethod
    def _profile_flutter(cls) -> LanguageProfile:
        pubspec = """name: mobile_service
description: Flutter and Dart Service
version: 1.0.0
environment:
  sdk: '>=3.0.0 <4.0.0'
dependencies:
  flutter:
    sdk: flutter
dev_dependencies:
  flutter_test:
    sdk: flutter
"""
        service_dart = """class ProcessingTask {
  final String taskId;
  String status;
  ProcessingTask({required this.taskId, this.status = 'pending'});
}

class CoreProcessingService {
  final String serviceName;
  final Map<String, ProcessingTask> _tasks = {};

  CoreProcessingService({this.serviceName = 'FlutterEngineService'});

  ProcessingTask submitTask(String taskId) {
    if (_tasks.containsKey(taskId)) throw ArgumentError('Task exists');
    final task = ProcessingTask(taskId: taskId);
    _tasks[taskId] = task;
    return task;
  }

  Map<String, dynamic> executeTask(String taskId) {
    final task = _tasks[taskId];
    if (task == null) throw StateError('Not found');
    task.status = 'completed';
    return {'status': 'completed'};
  }
}
"""
        test_dart = """import 'package:flutter_test/flutter_test.dart';
import '../lib/service.dart';

void main() {
  test('CoreProcessingService tests', () {
    final service = CoreProcessingService(serviceName: 'TestMobile');
    expect(service.serviceName, 'TestMobile');
    final task = service.submitTask('T-1');
    expect(task.status, 'pending');
    expect(service.executeTask('T-1')['status'], 'completed');
  });
}
"""
        dockerfile = "FROM dart:stable\nWORKDIR /app\nCOPY pubspec.yaml ./\nCOPY lib/ lib/\nCMD [\"dart\", \"run\", \"lib/main.dart\"]\n"
        return LanguageProfile(
            language="Dart",
            extension=".dart",
            build_file_name="pubspec.yaml",
            build_file_content=pubspec,
            service_file_name="lib/service.dart",
            service_code=service_dart,
            entrypoint_file_name="lib/main.dart",
            entrypoint_code="import 'service.dart';\nvoid main() { print('Started Dart Service'); }",
            test_framework="flutter test",
            test_file_name="test/service_test.dart",
            test_code=test_dart,
            docker_base_image="dart:stable",
            dockerfile_content=dockerfile,
            recommended_framework="Flutter 3.0+ / Bloc / Riverpod",
            paradigm="Reactive UI & Client-Side Logic",
            doc_urls=["https://docs.flutter.dev/"],
        )

    @classmethod
    def _profile_cpp(cls) -> LanguageProfile:
        cmakelists = "cmake_minimum_required(VERSION 3.20)\nproject(CoreService CXX)\nset(CMAKE_CXX_STANDARD 20)\n"
        service_cpp = """#include <string>
#include <unordered_map>
#include <stdexcept>

struct ProcessingTask {
    std::string taskId;
    std::string status;
};

class CoreProcessingService {
public:
    std::string serviceName;
    explicit CoreProcessingService(std::string name = "CppEngineService") : serviceName(std::move(name)) {}

    ProcessingTask submitTask(const std::string& taskId) {
        if (tasks.find(taskId) != tasks.end()) throw std::invalid_argument("Exists");
        ProcessingTask task{taskId, "pending"};
        tasks[taskId] = task;
        return task;
    }

    std::string executeTask(const std::string& taskId) {
        auto it = tasks.find(taskId);
        if (it == tasks.end()) throw std::runtime_error("Not found");
        it->second.status = "completed";
        return "completed";
    }

private:
    std::unordered_map<std::string, ProcessingTask> tasks;
};
"""
        test_cpp = """#include <cassert>
#include <iostream>
#include "../src/service.cpp"

int main() {
    CoreProcessingService service("TestCppService");
    assert(service.serviceName == "TestCppService");
    auto task = service.submitTask("T-1");
    assert(task.status == "pending");
    assert(service.executeTask("T-1") == "completed");
    std::cout << "All tests passed!" << std::endl;
    return 0;
}
"""
        dockerfile = "FROM gcc:13\nWORKDIR /app\nCOPY CMakeLists.txt ./\nCOPY src/ src/\nCOPY tests/ tests/\nCMD [\"gcc\", \"--version\"]\n"
        return LanguageProfile(
            language="C++",
            extension=".cpp",
            build_file_name="CMakeLists.txt",
            build_file_content=cmakelists,
            service_file_name="src/service.cpp",
            service_code=service_cpp,
            entrypoint_file_name="src/main.cpp",
            entrypoint_code="#include <iostream>\nint main() { std::cout << \"Started C++ Service\" << std::endl; return 0; }",
            test_framework="CMake / CTest",
            test_file_name="tests/test_service.cpp",
            test_code=test_cpp,
            docker_base_image="gcc:13",
            dockerfile_content=dockerfile,
            recommended_framework="STL / Boost / Qt",
            paradigm="Compiled High-Performance Systems",
            doc_urls=["https://en.cppreference.com/"],
        )

    @classmethod
    def _profile_csharp(cls) -> LanguageProfile:
        csproj = "<Project Sdk=\"Microsoft.NET.Sdk\">\n  <PropertyGroup>\n    <TargetFramework>net8.0</TargetFramework>\n  </PropertyGroup>\n</Project>\n"
        service_cs = """namespace CoreService;

public class ProcessingTask {
    public string TaskId { get; set; } = string.Empty;
    public string Status { get; set; } = "pending";
}

public class CoreProcessingService {
    public string ServiceName { get; }
    private readonly Dictionary<string, ProcessingTask> _tasks = new();

    public CoreProcessingService(string serviceName = "DotNetEngineService") {
        ServiceName = serviceName;
    }

    public ProcessingTask SubmitTask(string taskId) {
        if (_tasks.ContainsKey(taskId)) throw new InvalidOperationException("Exists");
        var task = new ProcessingTask { TaskId = taskId, Status = "pending" };
        _tasks[taskId] = task;
        return task;
    }

    public string ExecuteTask(string taskId) {
        if (!_tasks.TryGetValue(taskId, out var task)) throw new KeyNotFoundException("Not found");
        task.Status = "completed";
        return "completed";
    }
}
"""
        test_cs = """using Xunit;
using CoreService;

namespace CoreService.Tests;

public class ServiceTests {
    [Fact]
    public void TestExecution() {
        var service = new CoreProcessingService("TestService");
        Assert.Equal("TestService", service.ServiceName);
        var task = service.SubmitTask("T-1");
        Assert.Equal("pending", task.Status);
        Assert.Equal("completed", service.ExecuteTask("T-1"));
    }
}
"""
        dockerfile = "FROM mcr.microsoft.com/dotnet/sdk:8.0\nWORKDIR /app\nCOPY Service.csproj ./\nCOPY src/ src/\nCMD [\"dotnet\", \"test\"]\n"
        return LanguageProfile(
            language="C#",
            extension=".cs",
            build_file_name="Service.csproj",
            build_file_content=csproj,
            service_file_name="src/Service.cs",
            service_code=service_cs,
            entrypoint_file_name="src/Program.cs",
            entrypoint_code="using CoreService;\nConsole.WriteLine(\"Started .NET Service\");",
            test_framework="xUnit (dotnet test)",
            test_file_name="tests/ServiceTests.cs",
            test_code=test_cs,
            docker_base_image="mcr.microsoft.com/dotnet/sdk:8.0",
            dockerfile_content=dockerfile,
            recommended_framework="ASP.NET Core / Entity Framework",
            paradigm="Managed Enterprise Object-Oriented",
            doc_urls=["https://learn.microsoft.com/dotnet/"],
        )

    @classmethod
    def _profile_kotlin(cls) -> LanguageProfile:
        gradle = """plugins {
    kotlin("jvm") version "1.9.22"
}
repositories { mavenCentral() }
dependencies {
    testImplementation(kotlin("test"))
}
"""
        service_kt = """package coreservice

data class ProcessingTask(val taskId: String, var status: String = "pending")

class CoreProcessingService(val serviceName: String = "KotlinEngineService") {
    private val tasks = mutableMapOf<String, ProcessingTask>()

    fun submitTask(taskId: String): ProcessingTask {
        if (tasks.containsKey(taskId)) throw IllegalArgumentException("Exists")
        val task = ProcessingTask(taskId)
        tasks[taskId] = task
        return task
    }

    fun executeTask(taskId: String): String {
        val task = tasks[taskId] ?: throw NoSuchElementException("Not found")
        task.status = "completed"
        return "completed"
    }
}
"""
        test_kt = """package coreservice

import kotlin.test.Test
import kotlin.test.assertEquals

class ServiceTest {
    @Test
    fun testService() {
        val service = CoreProcessingService("TestKotlinService")
        assertEquals("TestKotlinService", service.serviceName)
        val task = service.submitTask("T-1")
        assertEquals("pending", task.status)
        assertEquals("completed", service.executeTask("T-1"))
    }
}
"""
        dockerfile = "FROM gradle:8-jdk17\nWORKDIR /app\nCOPY build.gradle.kts ./\nCOPY src/ src/\nCMD [\"gradle\", \"test\"]\n"
        return LanguageProfile(
            language="Kotlin",
            extension=".kt",
            build_file_name="build.gradle.kts",
            build_file_content=gradle,
            service_file_name="src/main/kotlin/Service.kt",
            service_code=service_kt,
            entrypoint_file_name="src/main/kotlin/Main.kt",
            entrypoint_code="package coreservice\nfun main() { println(\"Started Kotlin Service\") }",
            test_framework="kotlin.test (gradle test)",
            test_file_name="src/test/kotlin/ServiceTest.kt",
            test_code=test_kt,
            docker_base_image="gradle:8-jdk17",
            dockerfile_content=dockerfile,
            recommended_framework="Ktor / Spring Boot Kotlin",
            paradigm="Concise Static Pragmatic JVM",
            doc_urls=["https://kotlinlang.org/docs/"],
        )

    @classmethod
    def _profile_swift(cls) -> LanguageProfile:
        pkg_swift = """// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "CoreService",
    targets: [
        .target(name: "CoreService", path: "Sources"),
        .testTarget(name: "CoreServiceTests", dependencies: ["CoreService"], path: "Tests"),
    ]
)
"""
        service_swift = """public struct ProcessingTask {
    public let taskId: String
    public var status: String
}

public class CoreProcessingService {
    public let serviceName: String
    private var tasks: [String: ProcessingTask] = [:]

    public init(serviceName: String = "SwiftEngineService") {
        self.serviceName = serviceName
    }

    public func submitTask(taskId: String) -> ProcessingTask {
        let task = ProcessingTask(taskId: taskId, status: "pending")
        tasks[taskId] = task
        return task
    }

    public func executeTask(taskId: String) -> String {
        tasks[taskId]?.status = "completed"
        return "completed"
    }
}
"""
        test_swift = """import XCTest
@testable import CoreService

final class ServiceTests: XCTestCase {
    func testService() {
        let service = CoreProcessingService(serviceName: "TestSwiftService")
        XCTAssertEqual(service.serviceName, "TestSwiftService")
        let task = service.submitTask(taskId: "T-1")
        XCTAssertEqual(task.status, "pending")
        XCTAssertEqual(service.executeTask(taskId: "T-1"), "completed")
    }
}
"""
        dockerfile = "FROM swift:5.9\nWORKDIR /app\nCOPY Package.swift ./\nCOPY Sources/ Sources/\nCOPY Tests/ Tests/\nCMD [\"swift\", \"test\"]\n"
        return LanguageProfile(
            language="Swift",
            extension=".swift",
            build_file_name="Package.swift",
            build_file_content=pkg_swift,
            service_file_name="Sources/Service.swift",
            service_code=service_swift,
            entrypoint_file_name="Sources/main.swift",
            entrypoint_code="import CoreService\nprint(\"Started Swift Service\")",
            test_framework="XCTest (swift test)",
            test_file_name="Tests/ServiceTests.swift",
            test_code=test_swift,
            docker_base_image="swift:5.9",
            dockerfile_content=dockerfile,
            recommended_framework="Vapor / SwiftUI",
            paradigm="Protocol-Oriented & Value Types",
            doc_urls=["https://www.swift.org/documentation/"],
        )

    @classmethod
    def _profile_python(cls) -> LanguageProfile:
        pyproject = """[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "core_service"
version = "0.1.0"
description = "Core Business Processing Service"
dependencies = [
    "pydantic>=2.0.0",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
"""
        service_py = '''"""
Core service engine implementing the business logic for the system.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

@dataclass
class ProcessingTask:
    task_id: str
    payload: Dict[str, Any]
    status: str = "pending"
    result: Optional[Dict[str, Any]] = None

class CoreProcessingService:
    def __init__(self, service_name: str = "ADKEngineService") -> None:
        self.service_name = service_name
        self._tasks: Dict[str, ProcessingTask] = {}

    def submit_task(self, task_id: str, payload: Dict[str, Any]) -> ProcessingTask:
        if task_id in self._tasks:
            raise ValueError(f"Task with ID {task_id} already exists.")
        task = ProcessingTask(task_id=task_id, payload=payload)
        self._tasks[task_id] = task
        return task

    def execute_task(self, task_id: str) -> Dict[str, Any]:
        task = self._tasks.get(task_id)
        if not task:
            raise KeyError(f"Task {task_id} not found.")
        
        processed_data = {
            "processed_items": len(task.payload.get("items", [])),
            "status": "completed",
            "score": 1.0,
        }
        task.status = "completed"
        task.result = processed_data
        return processed_data

    def get_task(self, task_id: str) -> Optional[ProcessingTask]:
        return self._tasks.get(task_id)
'''
        test_py = '''"""
Unit test suite for CoreProcessingService.
"""
import pytest
from src.core.service import CoreProcessingService

def test_service_initialization():
    service = CoreProcessingService("TestService")
    assert service.service_name == "TestService"

def test_submit_and_execute_task():
    service = CoreProcessingService()
    task = service.submit_task("T-1", {"items": [1, 2, 3, 4]})
    assert task.status == "pending"

    res = service.execute_task("T-1")
    assert res["status"] == "completed"
    assert res["processed_items"] == 4
    assert service.get_task("T-1").status == "completed"

def test_duplicate_task_rejection():
    service = CoreProcessingService()
    service.submit_task("T-2", {})
    with pytest.raises(ValueError):
        service.submit_task("T-2", {})
'''
        dockerfile = """FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml .
COPY src/ src/
COPY tests/ tests/
RUN pip install --no-cache-dir pytest
CMD ["pytest", "tests/"]
"""
        return LanguageProfile(
            language="Python",
            extension=".py",
            build_file_name="pyproject.toml",
            build_file_content=pyproject,
            service_file_name="src/core/service.py",
            service_code=service_py,
            entrypoint_file_name="src/core/service.py",
            entrypoint_code=service_py,
            test_framework="pytest",
            test_file_name="tests/test_service.py",
            test_code=test_py,
            docker_base_image="python:3.12-slim",
            dockerfile_content=dockerfile,
            recommended_framework="FastAPI / Pydantic v2 / PyTorch",
            paradigm="High-Level Multi-Paradigm & Data Engineering",
            doc_urls=["https://docs.python.org/3/"],
        )

    @classmethod
    def _profile_generic(cls, custom_lang: str, doc_scraper: Optional[Any] = None) -> LanguageProfile:
        """
        Open-ended synthesizer for arbitrary/novel languages:
        Dynamically derives configurations, entrypoints, and test harnesses.
        """
        clean_name = re.sub(r"[^a-zA-Z0-9]", "", custom_lang).lower()
        ext = f".{clean_name[:4]}" if not clean_name.startswith(".") else clean_name

        build_file = f"{clean_name}.config"
        build_content = f"# Autonomous configuration manifest for {custom_lang}\nversion = 1.0\n"
        service_file = f"src/service{ext}"
        service_code = f"// Autonomous core service for {custom_lang}\n// Implements domain logic\nclass CoreProcessingService {{\n  public serviceName = \"{custom_lang}Service\";\n}}\n"
        test_file = f"tests/service_test{ext}"
        test_code = f"// Automated unit test suite for {custom_lang}\nassert(CoreProcessingService.serviceName == \"{custom_lang}Service\");\n"
        dockerfile = f"FROM {clean_name}:latest\nWORKDIR /app\nCOPY . .\nCMD [\"{clean_name}\", \"run\"]\n"

        return LanguageProfile(
            language=custom_lang,
            extension=ext,
            build_file_name=build_file,
            build_file_content=build_content,
            service_file_name=service_file,
            service_code=service_code,
            entrypoint_file_name=f"src/main{ext}",
            entrypoint_code=f"// Entrypoint for {custom_lang}\n",
            test_framework=f"{custom_lang} Native Test Runner",
            test_file_name=test_file,
            test_code=test_code,
            docker_base_image=f"{clean_name}:latest",
            dockerfile_content=dockerfile,
            recommended_framework=f"Standard {custom_lang} Ecosystem",
            paradigm=f"Modern {custom_lang} Paradigm",
            doc_urls=[],
        )


class DeveloperAgent(BaseAgent):
    name = "software_engineer"
    role_description = "Inżynier oprogramowania odpowiedzialny za czysty kod, testy jednostkowe i konfigurację środowiska w dowolnym języku"
    capabilities = ["code_generation", "unit_testing", "refactoring", "packaging", "polyglot_scaffolding", "framework_discovery"]

    def run(self, state: ADKProjectState, **kwargs: Any) -> ADKProjectState:
        state.record_event(
            event_type=EventType.STAGE_STARTED,
            stage_name="implementation",
            agent_name=self.name,
        )

        # Autonomiczny resolver profilu technologicznego (dowolny język / framework)
        doc_scraper = self.get_tool("doc_scraper")
        profile = DynamicLanguageResolver.resolve_profile(state, doc_scraper=doc_scraper)

        # Dynamiczna kompilacja promptu za pomocą DynamicPromptCompiler (REprompt / SOTA)
        from adk.engine.prompt_catalog import DynamicPromptCompiler
        prompts_dir = Path(__file__).resolve().parents[2] / "adk" / "prompts"
        compiler = DynamicPromptCompiler(prompts_dir)

        arch_summary = state.architecture.system_overview if state.architecture else "Standard Architecture"
        context_vars = {
            "architecture_spec": arch_summary,
            "target_language": profile.language,
            "test_framework": profile.test_framework,
            "recommended_framework": profile.recommended_framework,
        }

        compiled_prompt = compiler.compile_prompt("implementation", state, context_vars)

        # Wykonaj zapytanie do LLM (jeśli klient jest dostępny)
        if self.llm_client:
            self.llm_client.complete(
                prompt=compiled_prompt,
                system_prompt=f"You are a senior {profile.language} software engineer. Write idiomatic code, tests, and configuration for {profile.recommended_framework}.",
                agent_name=self.name
            )

        # Zarejestruj wygenerowane pliki scaffoldingu
        build_lang = profile.build_file_language or ("toml" if profile.build_file_name.endswith(".toml") else "json" if profile.build_file_name.endswith(".json") else "yaml" if profile.build_file_name.endswith((".yaml", ".yml")) else "cmake" if "cmake" in profile.build_file_name.lower() else profile.language.lower())
        state.add_artifact(profile.build_file_name, profile.build_file_content, f"Konfiguracja projektu {profile.language}", language=build_lang, is_test=False)
        state.add_artifact(profile.service_file_name, profile.service_code, f"Główny serwis logiki w {profile.language}", language=profile.language.lower(), is_test=False)
        if profile.entrypoint_file_name != profile.service_file_name:
            state.add_artifact(profile.entrypoint_file_name, profile.entrypoint_code, f"Punkt wejścia aplikacji {profile.language}", language=profile.language.lower(), is_test=False)
        state.add_artifact(profile.test_file_name, profile.test_code, f"Testy jednostkowe ({profile.test_framework})", language=profile.language.lower(), is_test=True)
        state.add_artifact("Dockerfile", profile.dockerfile_content, f"Wieloetapowy kontener Docker dla {profile.language}", language="dockerfile", is_test=False)

        # Dynamicznie wygeneruj treść Rozdziału 4 pracy dyplomowej (Implementacja)
        chapter_content = (
            f"W rozdziale opisano szczegóły techniczne implementacji oprogramowania w technologii **{profile.language}** "
            f"z wykorzystaniem ekosystemu **{profile.recommended_framework}** ({profile.paradigm}).\n\n"
            f"== Realizacja warstwy logiki biznesowej\n"
            f"Główny komponent przetwarzania danych został zaimplementowany w module `{profile.service_file_name}`. "
            f"Projekt wykorzystuje natywne mechanizmy języka {profile.language} gwarantujące wysoką wydajność, czytelność i bezpieczeństwo kodu.\n\n"
            f"== Zapewnienie jakości i testy jednostkowe\n"
            f"Do weryfikacji poprawności logiki biznesowej opracowano zestaw testów jednostkowych w module `{profile.test_file_name}` "
            f"uruchamianych za pomocą frameworka `{profile.test_framework}`.\n\n"
            f"== Konteneryzacja i środowisko uruchomieniowe\n"
            f"Przygotowano zoptymalizowany plik `Dockerfile` bazujący na obrazie `{profile.docker_base_image}`, "
            f"zapewniający powtarzalne środowisko uruchomieniowe i łatwe wdrożenie w infrastrukturze chmurowej."
        )

        state.chapters = [c for c in state.chapters if c.number != 4]
        state.chapters.append(
            ChapterDraft(
                number=4,
                title="Implementacja i środowisko uruchomieniowe",
                content_typst=chapter_content,
                content_latex=chapter_content,
                summary=f"Opis implementacji w języku {profile.language} ({profile.recommended_framework}), architektury modułów, testów i konteneryzacji.",
                code_snippets_referenced=[profile.service_file_name, profile.test_file_name, "Dockerfile"],
            )
        )

        state.notes.append(f"[{self.name}] Zaimplementowano projekt w ekosystemie {profile.language} ({profile.recommended_framework}) — {len(state.code_artifacts)} artefaktów.")
        state.current_stage = "benchmarks"
        if "implementation" not in state.completed_stages:
            state.completed_stages.append("implementation")

        state.record_event(
            event_type=EventType.STAGE_COMPLETED,
            stage_name="implementation",
            agent_name=self.name,
            payload={"language": profile.language, "framework": profile.recommended_framework},
        )
        return state
