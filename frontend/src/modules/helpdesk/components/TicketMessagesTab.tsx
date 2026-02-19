/**
 * AZALSCORE Module - Helpdesk - Ticket Messages Tab
 * Onglet conversation du ticket
 */

import React, { useState } from 'react';
import {
  MessageSquare, Send, Lock, User, Clock, Paperclip
} from 'lucide-react';
import { Button } from '@ui/actions';
import { Card } from '@ui/layout';
import { formatDateTime } from '@/utils/formatters';
import { getPublicMessageCount, getInternalMessageCount } from '../types';
import type { Ticket, TicketMessage } from '../types';
import type { TabContentProps } from '@ui/standards';

/**
 * TicketMessagesTab - Conversation du ticket
 */
export const TicketMessagesTab: React.FC<TabContentProps<Ticket>> = ({ data: ticket }) => {
  const [newMessage, setNewMessage] = useState('');
  const [isInternal, setIsInternal] = useState(false);
  const [isSending, setIsSending] = useState(false);

  const messages = ticket.messages || [];
  const publicCount = getPublicMessageCount(ticket);
  const internalCount = getInternalMessageCount(ticket);

  const handleSend = async () => {
    if (!newMessage.trim()) return;
    setIsSending(true);
    // API call would go here
    setTimeout(() => {
      setIsSending(false);
      setNewMessage('');
    }, 1000);
  };

  return (
    <div className="azals-std-tab-content">
      {/* Resume */}
      <div className="flex gap-4 mb-4">
        <div className="azals-stat-mini">
          <MessageSquare size={16} className="text-blue-500" />
          <span>{publicCount} message(s) public(s)</span>
        </div>
        <div className="azals-stat-mini">
          <Lock size={16} className="text-yellow-500" />
          <span>{internalCount} note(s) interne(s)</span>
        </div>
      </div>

      {/* Conversation */}
      <Card title="Conversation" icon={<MessageSquare size={18} />}>
        {messages.length > 0 ? (
          <div className="azals-messages-list">
            {messages.map((msg) => (
              <MessageItem key={msg.id} message={msg} />
            ))}
          </div>
        ) : (
          <div className="azals-empty azals-empty--sm">
            <MessageSquare size={32} className="text-muted" />
            <p className="text-muted">Aucun message</p>
          </div>
        )}

        {/* Formulaire de reponse */}
        <div className="azals-message-form mt-4 pt-4 border-t">
          <div className="azals-form-field">
            <span className="azals-field__label">Nouvelle reponse</span>
            <textarea
              className="azals-textarea"
              value={newMessage}
              onChange={(e) => setNewMessage(e.target.value)}
              rows={4}
              placeholder="Ecrivez votre message..."
            />
          </div>
          <div className="flex items-center justify-between mt-2">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={isInternal}
                onChange={(e) => setIsInternal(e.target.checked)}
                className="azals-checkbox"
              />
              <Lock size={14} className="text-yellow-500" />
              <span className="text-sm">Note interne (non visible par le client)</span>
            </label>
            <div className="flex gap-2">
              <Button variant="ghost" leftIcon={<Paperclip size={16} />} onClick={() => { window.dispatchEvent(new CustomEvent('azals:action', { detail: { type: 'attachFile', ticketId: ticket.id } })); }}>
                Joindre
              </Button>
              <Button
                onClick={handleSend}
                disabled={!newMessage.trim() || isSending}
                leftIcon={<Send size={16} />}
              >
                {isSending ? 'Envoi...' : 'Envoyer'}
              </Button>
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
};

/**
 * Composant message
 */
const MessageItem: React.FC<{ message: TicketMessage }> = ({ message }) => {
  return (
    <div className={`azals-message ${message.is_internal ? 'azals-message--internal' : ''}`}>
      <div className="azals-message__header">
        <div className="azals-message__author">
          <User size={14} />
          <span className="font-medium">{message.author_name || 'Anonyme'}</span>
          {message.author_email && (
            <span className="text-muted text-sm">({message.author_email})</span>
          )}
        </div>
        <div className="azals-message__meta">
          {message.is_internal && (
            <span className="azals-badge azals-badge--yellow azals-badge--sm mr-2">
              <Lock size={10} className="mr-1" />
              Interne
            </span>
          )}
          <span className="text-muted text-sm flex items-center gap-1">
            <Clock size={12} />
            {formatDateTime(message.created_at)}
          </span>
        </div>
      </div>
      <div className="azals-message__content">
        <p className="whitespace-pre-wrap">{message.content}</p>
      </div>
      {message.attachments && message.attachments.length > 0 && (
        <div className="azals-message__attachments">
          {message.attachments.map((att) => (
            <a
              key={att.id}
              href={att.file_url}
              className="azals-attachment-link"
              target="_blank"
              rel="noopener noreferrer"
            >
              <Paperclip size={12} />
              <span>{att.name}</span>
            </a>
          ))}
        </div>
      )}
    </div>
  );
};

export default TicketMessagesTab;
