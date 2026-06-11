export const sampleModels = [
  {
    label: 'STEP cube',
    path: '/samples/simple-cube.step',
    format: 'STEP',
    description: 'Valid AP214 B-rep cube tessellated in-browser with OpenCascade.',
  },
  {
    label: 'Generated bracket STL',
    path: '/samples/generated-bracket.stl',
    format: 'STL',
    description: 'Lightweight triangulated bracket for quick mesh loading.',
  },
  {
    label: 'Tiny assembly glTF',
    path: '/samples/tiny-assembly.gltf',
    format: 'glTF',
    description: 'Compact multi-part mesh assembly with external binary buffer.',
  },
] as const;
