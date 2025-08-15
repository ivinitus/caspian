import React, { useState } from 'react';
import { SafeAreaView, Text, StyleSheet, TextInput, TouchableOpacity, FlatList, View, ActivityIndicator } from 'react-native';

const API_URL = process.env.EXPO_PUBLIC_API_URL || 'http://localhost:8000';

export default function App() {
  const [messages, setMessages] = useState([
    { role: 'assistant', content: 'Hello Sir, I am Caspian. How may I assist you today?' },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  const sendMessage = async () => {
    if (!input.trim() || loading) return;
    const userMsg = { role: 'user', content: input };
    const newMessages = [...messages, userMsg];
    setMessages(newMessages);
    setInput('');
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/llm/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ messages: newMessages }),
      });
      const data = await res.json();
      const reply = data.text || data.reply || 'Sorry Sir, I could not process that.';
      setMessages([...newMessages, { role: 'assistant', content: reply }]);
    } catch (e) {
      setMessages([...newMessages, { role: 'assistant', content: 'Sorry Sir, there was an error.' }]);
    }
    setLoading(false);
  };

  const renderItem = ({ item }) => (
    <View style={[styles.bubble, item.role === 'user' ? styles.bubbleUser : styles.bubbleAssistant]}>
      <Text style={styles.bubbleText}>{item.content}</Text>
    </View>
  );

  return (
    <SafeAreaView style={styles.container}>
      <Text style={styles.title}>Caspian AI Assistant</Text>
      <FlatList
        data={messages}
        renderItem={renderItem}
        keyExtractor={(_, idx) => String(idx)}
        contentContainerStyle={styles.list}
      />
      {loading && <ActivityIndicator style={{ margin: 8 }} />}
      <View style={styles.inputRow}>
        <TextInput
          style={styles.input}
          value={input}
          onChangeText={setInput}
          placeholder="Type your message, Sir…"
          editable={!loading}
        />
        <TouchableOpacity style={styles.button} onPress={sendMessage} disabled={loading || !input.trim()}>
          <Text style={styles.buttonText}>Send</Text>
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    padding: 16,
  },
  list: {
    padding: 16,
  },
  bubble: {
    padding: 12,
    borderRadius: 12,
    marginBottom: 8,
    maxWidth: '85%',
  },
  bubbleUser: {
    backgroundColor: '#d1e7ff',
    alignSelf: 'flex-end',
  },
  bubbleAssistant: {
    backgroundColor: '#f0f0f0',
    alignSelf: 'flex-start',
  },
  bubbleText: {
    fontSize: 16,
  },
  inputRow: {
    flexDirection: 'row',
    padding: 12,
    borderTopWidth: 1,
    borderTopColor: '#eee',
  },
  input: {
    flex: 1,
    borderWidth: 1,
    borderColor: '#ccc',
    borderRadius: 8,
    paddingHorizontal: 12,
    height: 44,
  },
  button: {
    marginLeft: 8,
    backgroundColor: '#0d6efd',
    borderRadius: 8,
    paddingHorizontal: 16,
    justifyContent: 'center',
  },
  buttonText: {
    color: '#fff',
    fontWeight: '600',
  },
});
