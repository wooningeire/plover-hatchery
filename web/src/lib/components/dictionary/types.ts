export type CompileState = "idle" | "compiling" | "compiled" | "error";
export type CompileAction = "compile" | "refresh";
export type PloverConnectionState = "checking" | "connected" | "error";
export type DictionaryLoadState = "loading" | "loaded" | "error";
export type EntryLoadState = "idle" | "loading" | "loaded" | "error";
export type SaveState = "idle" | "saving" | "saved" | "error";


export const ENTRY_PAGE_LIMIT = 100;
