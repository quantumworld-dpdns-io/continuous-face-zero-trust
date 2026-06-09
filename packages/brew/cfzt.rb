# Documentation for Continuous Face Zero Trust formula
class Cfzt < Formula
  desc "Continuous Face Zero Trust CLI and SDK"
  homepage "https://github.com/cfzt/continuous-face-zero-trust"
  url "https://github.com/cfzt/continuous-face-zero-trust/archive/v1.0.0.tar.gz"
  sha256 "0000000000000000000000000000000000000000000000000000000000000000"
  license "MIT"
  depends_on "python@3.10"
  depends_on "openssl@3"
  depends_on "cmake" => :build

  def install
    system "python3", "-m", "pip", "install", *std_pip_args, "."
    system "cmake", "-S", ".", "-B", "build", *std_cmake_args
    system "cmake", "--build", "build"
    system "cmake", "--install", "build", prefix: libexec
    bin.install_symlink Dir[libexec/"bin/*"]
  end

  test do
    system "#{bin}/cfzt", "--version"
    system "#{bin}/cfzt", "health"
  end
end
