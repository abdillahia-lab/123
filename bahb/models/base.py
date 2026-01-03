"""Base model classes and utilities for BAHB AI pipeline."""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Optional, TypeVar

import numpy as np
from numpy.typing import NDArray
from loguru import logger

T = TypeVar("T")


class BaseModel(ABC):
    """Abstract base class for all AI models."""

    def __init__(
        self,
        model_path: str | Path,
        device: str = "cuda:0",
        half_precision: bool = True,
    ):
        self.model_path = Path(model_path)
        self.device = device
        self.half_precision = half_precision
        self._model: Any = None
        self._is_loaded = False

        # Performance tracking
        self._inference_times: list[float] = []
        self._max_history = 100

    @property
    def is_loaded(self) -> bool:
        return self._is_loaded

    @property
    def avg_inference_time(self) -> float:
        if not self._inference_times:
            return 0.0
        return sum(self._inference_times) / len(self._inference_times)

    @abstractmethod
    def load(self) -> bool:
        """Load model weights and initialize."""
        pass

    @abstractmethod
    def unload(self) -> None:
        """Unload model and free resources."""
        pass

    @abstractmethod
    def preprocess(self, image: NDArray) -> Any:
        """Preprocess image for inference."""
        pass

    @abstractmethod
    def forward(self, inputs: Any) -> Any:
        """Run model inference."""
        pass

    @abstractmethod
    def postprocess(self, outputs: Any, original_shape: tuple) -> Any:
        """Postprocess model outputs."""
        pass

    def __call__(self, image: NDArray) -> Any:
        """Run full inference pipeline with timing."""
        if not self._is_loaded:
            raise RuntimeError("Model not loaded. Call load() first.")

        start_time = time.perf_counter()

        # Run pipeline
        original_shape = image.shape[:2]
        inputs = self.preprocess(image)
        outputs = self.forward(inputs)
        results = self.postprocess(outputs, original_shape)

        # Track timing
        elapsed = (time.perf_counter() - start_time) * 1000  # ms
        self._inference_times.append(elapsed)
        if len(self._inference_times) > self._max_history:
            self._inference_times.pop(0)

        return results

    def warmup(self, input_shape: tuple[int, int, int] = (640, 640, 3)) -> None:
        """Warmup model with dummy input."""
        if not self._is_loaded:
            return

        logger.info(f"Warming up {self.__class__.__name__}...")
        dummy = np.zeros(input_shape, dtype=np.uint8)
        for _ in range(3):
            self(dummy)
        self._inference_times.clear()
        logger.info(f"{self.__class__.__name__} warmup complete")


class ModelRegistry:
    """Registry for managing multiple AI models."""

    _instance: Optional["ModelRegistry"] = None
    _models: dict[str, BaseModel] = {}

    def __new__(cls) -> "ModelRegistry":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def register(cls, name: str, model: BaseModel) -> None:
        """Register a model instance."""
        cls._models[name] = model
        logger.info(f"Registered model: {name}")

    @classmethod
    def get(cls, name: str) -> Optional[BaseModel]:
        """Get a registered model."""
        return cls._models.get(name)

    @classmethod
    def load_all(cls) -> None:
        """Load all registered models."""
        for name, model in cls._models.items():
            if not model.is_loaded:
                logger.info(f"Loading model: {name}")
                model.load()

    @classmethod
    def unload_all(cls) -> None:
        """Unload all models."""
        for name, model in cls._models.items():
            if model.is_loaded:
                logger.info(f"Unloading model: {name}")
                model.unload()

    @classmethod
    def get_stats(cls) -> dict[str, dict]:
        """Get statistics for all models."""
        return {
            name: {
                "loaded": model.is_loaded,
                "avg_inference_ms": model.avg_inference_time,
            }
            for name, model in cls._models.items()
        }


class TensorRTModel(BaseModel):
    """Base class for TensorRT-optimized models."""

    def __init__(
        self,
        model_path: str | Path,
        device: str = "cuda:0",
        workspace_size: int = 1 << 30,  # 1GB
    ):
        super().__init__(model_path, device, half_precision=True)
        self.workspace_size = workspace_size
        self._engine = None
        self._context = None
        self._bindings: list = []
        self._stream = None

    def load(self) -> bool:
        """Load TensorRT engine."""
        try:
            import tensorrt as trt
            import pycuda.driver as cuda
            import pycuda.autoinit  # noqa

            # Check for engine file
            engine_path = self.model_path
            if not engine_path.exists():
                logger.error(f"Engine file not found: {engine_path}")
                return False

            # Load engine
            logger.info(f"Loading TensorRT engine: {engine_path}")
            with open(engine_path, "rb") as f:
                runtime = trt.Runtime(trt.Logger(trt.Logger.WARNING))
                self._engine = runtime.deserialize_cuda_engine(f.read())

            if self._engine is None:
                logger.error("Failed to deserialize engine")
                return False

            # Create execution context
            self._context = self._engine.create_execution_context()

            # Allocate buffers
            self._allocate_buffers()

            # Create CUDA stream
            self._stream = cuda.Stream()

            self._is_loaded = True
            logger.info(f"TensorRT engine loaded successfully")
            return True

        except ImportError:
            logger.warning("TensorRT not available, falling back to ONNX")
            return self._load_onnx_fallback()
        except Exception as e:
            logger.error(f"Failed to load TensorRT engine: {e}")
            return False

    def _allocate_buffers(self) -> None:
        """Allocate input/output buffers."""
        import pycuda.driver as cuda
        import tensorrt as trt

        self._bindings = []
        self._inputs = []
        self._outputs = []

        for i in range(self._engine.num_io_tensors):
            name = self._engine.get_tensor_name(i)
            shape = self._engine.get_tensor_shape(name)
            dtype = trt.nptype(self._engine.get_tensor_dtype(name))
            size = np.prod(shape) * np.dtype(dtype).itemsize

            # Allocate device memory
            device_mem = cuda.mem_alloc(int(size))
            host_mem = cuda.pagelocked_empty(int(np.prod(shape)), dtype)

            binding = {
                "name": name,
                "shape": shape,
                "dtype": dtype,
                "device": device_mem,
                "host": host_mem,
            }

            if self._engine.get_tensor_mode(name) == trt.TensorIOMode.INPUT:
                self._inputs.append(binding)
            else:
                self._outputs.append(binding)

            self._bindings.append(int(device_mem))

    def _load_onnx_fallback(self) -> bool:
        """Load ONNX model as fallback."""
        try:
            import onnxruntime as ort

            onnx_path = self.model_path.with_suffix(".onnx")
            if not onnx_path.exists():
                logger.error(f"ONNX file not found: {onnx_path}")
                return False

            providers = ["CUDAExecutionProvider", "CPUExecutionProvider"]
            self._model = ort.InferenceSession(str(onnx_path), providers=providers)
            self._is_loaded = True
            logger.info("Loaded ONNX model as fallback")
            return True
        except Exception as e:
            logger.error(f"Failed to load ONNX fallback: {e}")
            return False

    def unload(self) -> None:
        """Free TensorRT resources."""
        if self._context:
            del self._context
        if self._engine:
            del self._engine
        self._bindings.clear()
        self._is_loaded = False
