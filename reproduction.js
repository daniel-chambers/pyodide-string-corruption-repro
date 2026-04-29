import { loadPyodide } from "pyodide";
import { readFileSync } from "fs";

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

const file = readFileSync("./reproduction.py", { encoding: "utf8" });
pyodide.runPython(file);