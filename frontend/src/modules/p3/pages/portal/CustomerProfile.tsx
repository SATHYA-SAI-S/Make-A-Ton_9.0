import React, { useEffect, useState } from 'react';
import { User, Building2, Mail, Phone, MapPin, ShieldCheck, Save } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent, Input, Button, Badge, useToast } from '@/shared/ui';
import { portalApi } from '../../api/portalApi';
import { CustomerProfile } from '../../types/portal';

export const CustomerProfilePage: React.FC = () => {
  const { toast } = useToast();
  const [profile, setProfile] = useState<CustomerProfile | null>(null);
  const [phone, setPhone] = useState('');
  const [address, setAddress] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    portalApi
      .getProfile()
      .then((res) => {
        setProfile(res);
        setPhone(res.phone || '');
        setAddress(res.billing_address || '');
      })
      .catch((err) => toast.error('Failed to load profile', err.message))
      .finally(() => setIsLoading(false));
  }, []);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    try {
      const updated = await portalApi.updateProfile({
        phone: phone || undefined,
        billing_address: address || undefined,
      });
      setProfile(updated);
      toast.success('Profile Updated', 'Contact and billing details saved.');
    } catch (err: any) {
      toast.error('Update Failed', err.message);
    } finally {
      setIsSaving(false);
    }
  };

  if (isLoading) {
    return <div className="py-12 text-center text-xs text-slate-400">Loading profile data...</div>;
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
          Account & Billing Profile
        </h1>
        <p className="text-xs text-slate-500">
          Manage your organization details and dispatch address for official tax receipts.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Left Side: Identity Snapshot */}
        <Card className="p-6 space-y-4">
          <div className="w-16 h-16 rounded-2xl bg-brand-50 dark:bg-brand-950/60 text-brand-600 dark:text-brand-300 flex items-center justify-center font-bold text-xl">
            {profile?.name.substring(0, 2).toUpperCase() || 'CU'}
          </div>

          <div>
            <h3 className="font-bold text-base text-slate-900 dark:text-slate-100">{profile?.name}</h3>
            <p className="text-xs text-slate-400">{profile?.email}</p>
          </div>

          <div className="pt-3 border-t border-slate-100 dark:border-slate-800 space-y-2 text-xs">
            <div className="flex justify-between items-center">
              <span className="text-slate-400">Tier Segment:</span>
              <Badge variant="brand" size="sm">
                {profile?.segment}
              </Badge>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-slate-400">Account Status:</span>
              <Badge variant="success" size="sm" dot>
                {profile?.status}
              </Badge>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-slate-400">GSTIN Registered:</span>
              <span className="font-mono font-medium">{profile?.gstin || 'None'}</span>
            </div>
          </div>
        </Card>

        {/* Right Side: Editable Details Form */}
        <div className="md:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle>Editable Contact Information</CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSave} className="space-y-4">
                <Input
                  label="Registered Organization Name"
                  value={profile?.name || ''}
                  disabled
                  helperText="Organization legal title cannot be modified online. Contact account manager."
                />

                <Input
                  label="Registered Email (Login ID)"
                  value={profile?.email || ''}
                  disabled
                  helperText="Primary email used for billing notifications."
                />

                <Input
                  label="Primary Contact Phone"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  placeholder="+91 98765 43210"
                />

                <div className="space-y-1.5">
                  <label className="block text-xs font-semibold uppercase tracking-wider text-slate-700 dark:text-slate-300">
                    Official Billing & Invoicing Address
                  </label>
                  <textarea
                    rows={3}
                    value={address}
                    onChange={(e) => setAddress(e.target.value)}
                    className="w-full text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 p-3 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-brand-500"
                    placeholder="Enter full physical address with state and postal code..."
                  />
                </div>

                <div className="flex justify-end pt-2">
                  <Button
                    type="submit"
                    variant="primary"
                    isLoading={isSaving}
                    leftIcon={<Save className="w-4 h-4" />}
                  >
                    Save Changes
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};
