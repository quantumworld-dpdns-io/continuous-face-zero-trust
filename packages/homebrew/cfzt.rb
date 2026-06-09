class Cfzt < Formula
  desc = "Continuous Face Zero Trust — CLI tool"
  homepage = "https://github.com/quantumworld-dpdns-io/continuous-face-zero-trust"
  url "https://github.com/quantumworld-dpdns-io/continuous-face-zero-trust/releases/download/v0.1.0/cfzt-darwin-arm64.tar.gz"
  sha256 "PLACEHOLDER"
  license "MIT"

  depends_on "python@3.12"

  def install
    bin.install "cfzt"
  end

  test do
    assert_match "cfzt", shell_output("#{bin}/cfzt --version")
  end
end
