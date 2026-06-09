export enum ErrorCode {
  UNSPECIFIED = "UNSPECIFIED",
  UNAUTHENTICATED = "UNAUTHENTICATED",
  UNAUTHORIZED = "UNAUTHORIZED",
  NOT_FOUND = "NOT_FOUND",
  INVALID_ARGUMENT = "INVALID_ARGUMENT",
  RATE_LIMITED = "RATE_LIMITED",
  INTERNAL = "INTERNAL",
}

export class CFZTError extends Error {
  public code: ErrorCode;
  public details: Record<string, string>;

  constructor(message: string, code: ErrorCode = ErrorCode.INTERNAL, details: Record<string, string> = {}) {
    super(message);
    this.name = "CFZTError";
    this.code = code;
    this.details = details;
  }

  toJSON() {
    return { error: { code: this.code, message: this.message, details: this.details } };
  }
}
