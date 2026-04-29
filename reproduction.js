import { loadPyodide } from "pyodide";
import "pyodide/pyodide.asm.js";
import { readFile } from "fs/promises";

function inspectStr(s) {
    let nulCount = 0;
    for (let i = 0; i < s.length; i++) {
        if (s.charCodeAt(i) === 0) nulCount++;
    }
    return {
        length: s.length,
        nulCount: nulCount,
        firstCode: s.length > 0 ? s.charCodeAt(0) : -1,
    };
};

const pyodide = await loadPyodide({
  jsglobals: {
    inspectStr,
  },
});

const file = await readFile("./reproduction.py", { encoding: "utf8" });
await pyodide.runPythonAsync(file);