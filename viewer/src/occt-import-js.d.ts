declare module 'occt-import-js' {
  export interface OcctImportMesh {
    name?: string;
    color?: [number, number, number];
    attributes: {
      position: { array: number[] };
      normal?: { array: number[] };
    };
    index?: { array: number[] };
  }

  export interface OcctImportResult {
    success: boolean;
    error?: string;
    root?: unknown;
    meshes?: OcctImportMesh[];
  }

  export interface OcctModule {
    ReadStepFile(content: Uint8Array, params: Record<string, unknown> | null): OcctImportResult;
  }

  export interface OcctModuleOptions {
    locateFile?: (path: string) => string;
    print?: (...args: unknown[]) => void;
    printErr?: (...args: unknown[]) => void;
  }

  export default function occtImportJs(options?: OcctModuleOptions): Promise<OcctModule>;
}
