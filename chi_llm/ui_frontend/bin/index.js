#!/usr/bin/env node
import React, {useEffect, useState} from 'react';
import {render, Box, Text, useInput} from 'ink';
import SelectInput from 'ink-select-input';
import {execFile} from 'node:child_process';

const runCli = (args) => new Promise((resolve) => {
  execFile('chi-llm', args, {encoding: 'utf8'}, (err, stdout, stderr) => {
    resolve({err, stdout, stderr});
  });
});

const useQuitKey = () => {
  useInput((input, key) => {
    if (input === 'q' || key.escape) {
      process.exit(0);
    }
  });
};

const ModelsScreen = ({onBack}) => {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [msg, setMsg] = useState('');

  useEffect(() => {
    (async () => {
      const {stdout} = await runCli(['models', 'list', '--json']);
      try {
        const data = JSON.parse(stdout || '[]');
        const mapped = data.map((m) => ({
          label: `${m.current ? '★ ' : ''}${m.name} [${m.id}] ${m.downloaded ? '✓' : ''}`,
          value: m.id
        }));
        setItems(mapped);
      } catch (e) {
        setMsg('Failed to parse models list.');
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const onSelect = async (item) => {
    setMsg('Setting model...');
    const {stderr} = await runCli(['models', 'set', item.value, '--local']);
    setMsg(stderr ? stderr.trim() : 'Model set for this project.');
  };

  return (
    <Box flexDirection="column">
      <Text bold>Models</Text>
      {loading ? <Text>Loading...</Text> : (
        items.length > 0 ? <SelectInput items={items} onSelect={onSelect}/> : <Text>No models found.</Text>
      )}
      {msg ? <Text color="gray">{msg}</Text> : null}
      <Text>Press Esc to go back, q to quit.</Text>
    </Box>
  );
};

const ConfigScreen = ({onBack}) => (
  <Box flexDirection="column">
    <Text bold>Config (coming soon)</Text>
    <Text color="gray">Edit temperature, max_tokens and provider settings with live validation.</Text>
    <Text>Press Esc to go back, q to quit.</Text>
  </Box>
);

const Dashboard = () => {
  useQuitKey();
  const [screen, setScreen] = useState('menu');
  const items = [
    {label: 'Bootstrap', value: 'bootstrap'},
    {label: 'Models', value: 'models'},
    {label: 'Config', value: 'config'},
    {label: 'Quit', value: 'quit'}
  ];

  const onSelect = async (item) => {
    if (item.value === 'quit') process.exit(0);
    if (item.value === 'bootstrap') {
      // Minimal bootstrap: generate .chi_llm.json with current model
      await runCli(['bootstrap', '.']);
      return;
    }
    setScreen(item.value);
  };

  if (screen === 'models') return <ModelsScreen onBack={() => setScreen('menu')}/>;
  if (screen === 'config') return <ConfigScreen onBack={() => setScreen('menu')}/>;

  return (
    <Box flexDirection="column">
      <Text bold>chi_llm Control Center</Text>
      <Text color="gray">Use arrows/enter to navigate. q/Esc to exit.</Text>
      <Box marginTop={1}>
        <SelectInput items={items} onSelect={onSelect}/>
      </Box>
    </Box>
  );
};

render(<Dashboard/>);
